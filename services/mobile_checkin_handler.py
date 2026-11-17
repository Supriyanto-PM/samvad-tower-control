"""
Native Standalone Mobile Field Check-In HTTP & API Handlers.
Intercepts mobile check-in requests before Streamlit to provide:
1. Ultra-fast, zero-overhead standalone mobile page (no iframes, no sandbox).
2. Direct 1-tap browser GPS permission and instant transmission to PMO Radar.
3. Simple JSON API for live telemetry updates.
Strictly icon-free enterprise typography.
"""

import json
import gc
from typing import Optional, Dict, Any

try:
    import tornado.web
    from tornado.routing import Matcher, Rule, PathMatches
    _RequestHandler = tornado.web.RequestHandler
    _Matcher = Matcher
    HAS_TORNADO = True
except ImportError:
    tornado = None
    HAS_TORNADO = False
    _RequestHandler = object
    _Matcher = object
    Rule = None
    PathMatches = None

from database.connection import query_df
from services.fleet_tracking_service import FleetTrackingService


import io
import wave

class SilenceAudioHandler(_RequestHandler):
    """
    Serves a valid 2-second silent WAV file with Accept-Ranges and Content-Length.
    Ensures iOS WebKit and Android media sessions remain active in the background
    when the phone screen is locked or stored in the technician's pocket.
    """
    _wav_cache = None

    @classmethod
    def get_wav_bytes(cls) -> bytes:
        if cls._wav_cache is None:
            buf = io.BytesIO()
            with wave.open(buf, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(1)
                wav.setframerate(8000)
                wav.writeframes(b'\x80' * 8000 * 2)
            cls._wav_cache = buf.getvalue()
        return cls._wav_cache

    def get(self):
        data = self.get_wav_bytes()
        self.set_header("Content-Type", "audio/wav")
        self.set_header("Content-Length", str(len(data)))
        self.set_header("Cache-Control", "public, max-age=86400")
        self.set_header("Accept-Ranges", "bytes")
        self.write(data)


class MobileMatcher(_Matcher):
    """
    Matches requests destined for the mobile technician check-in portal:
    - /checkin
    - /m/checkin
    - /?checkin=... (direct links opened from WhatsApp)
    """
    def match(self, request):
        path = request.path.rstrip('/')
        if path in ('/checkin', '/m/checkin'):
            return {}
        if path == '' or path == '/':
            if 'checkin=' in request.query:
                return {}
        return None


class CheckinApiHandler(_RequestHandler):
    """
    JSON API endpoint for mobile GPS telemetry transmission.
    Receives live coordinates and updates the PMO Radar database directly.
    """
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.set_header("Content-Type", "application/json")

    def options(self):
        self.set_status(204)
        self.finish()

    def get(self):
        self.handle_telemetry()

    def post(self):
        self.handle_telemetry()

    def handle_telemetry(self):
        try:
            body = self.request.body.decode("utf-8")
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        # Support batch offline sync when phone reconnects after server sleep or dead zone
        batch = data.get("batch")
        if isinstance(batch, list) and batch:
            batch_uuid = str(data.get("client_uuid") or data.get("device_uuid") or data.get("device_id") or "").strip()
            if batch_uuid and len(batch) > 0:
                first_pt = batch[0]
                p_code = str(first_pt.get("team_code") or "TEAM-MW017").strip().upper()
                p_site = str(first_pt.get("site_id") or "DAX001").strip().upper()
                is_auth, reason, dev_info = FleetTrackingService.verify_or_bind_device(
                    team_code=p_code,
                    site_id=p_site,
                    device_id=batch_uuid,
                    user_agent=self.request.headers.get("User-Agent", "OfflineSync/1.0")
                )
                if not is_auth:
                    self.set_status(403)
                    self.write(json.dumps({
                        "success": False,
                        "access_denied": True,
                        "message": dev_info.get("message", "ACCESS DENIED: Unauthorized device.")
                    }))
                    return

            synced = 0
            for pt in batch:
                try:
                    p_code = str(pt.get("team_code") or "TEAM-MW017").strip().upper()
                    p_site = str(pt.get("site_id") or "DAX001").strip().upper()
                    p_lat = float(pt.get("lat"))
                    p_lon = float(pt.get("lon"))
                    p_acc = float(pt.get("accuracy_m", 10.0))
                    p_stat = str(pt.get("status", "Confirmed - En Route")).strip()
                    FleetTrackingService.record_team_checkin(
                        team_code=p_code,
                        site_id=p_site,
                        lat=p_lat,
                        lon=p_lon,
                        status=p_stat,
                        accuracy_m=p_acc,
                        user_agent=self.request.headers.get("User-Agent", "OfflineSync/1.0"),
                        notes="Offline queue sync after server sleep / reconnect"
                    )
                    synced += 1
                except Exception:
                    pass
            self.write(json.dumps({
                "success": True,
                "synced_count": synced,
                "message": f"Synced {synced} queued offline points successfully"
            }))
            return

        # Support both standard checkin and Traccar/OsmAnd background tracker protocol ('id', 'device_id')
        raw_code = (
            data.get("team_code") or 
            data.get("id") or 
            data.get("device_id") or 
            self.get_argument("team_code", None) or 
            self.get_argument("id", None) or 
            self.get_argument("device_id", "TEAM-MW017")
        )
        team_code = str(raw_code).strip().upper()

        # Check if PMO Controller has officially terminated tracking for this crew
        df_crew = query_df("SELECT checkin_status, status FROM paas_field_teams WHERE team_code = ? LIMIT 1", (team_code,))
        if not df_crew.empty:
            c_stat = str(df_crew.iloc[0]["checkin_status"] or "")
            if "closed by pmo" in c_stat.lower() or "terminated" in c_stat.lower():
                self.write(json.dumps({
                    "success": True,
                    "tracking_active": False,
                    "controller_terminated": True,
                    "message": "Assignment has been officially closed by PMO Controller. Background tracking terminated."
                }))
                return

        raw_site = data.get("site_id") or self.get_argument("site_id", None)
        if raw_site:
            site_id = str(raw_site).strip().upper()
        else:
            # Auto-lookup assigned site from database for this crew
            df_asg = query_df("SELECT last_checkin_site FROM paas_field_teams WHERE team_code = ? LIMIT 1", (team_code,))
            if not df_asg.empty and df_asg.iloc[0]["last_checkin_site"]:
                site_id = str(df_asg.iloc[0]["last_checkin_site"]).strip().upper()
            else:
                df_asg2 = query_df("SELECT site_id FROM timor_sites_100 WHERE assigned_team = ? LIMIT 1", (team_code,))
                site_id = str(df_asg2.iloc[0]["site_id"]).strip().upper() if not df_asg2.empty else "DAX001"

        # Enforce 1-Device Binding and Anti-Share Limitation
        client_uuid = str(data.get("client_uuid") or data.get("device_uuid") or (data.get("device_id") if data.get("device_id") != team_code else "") or self.get_argument("client_uuid", "")).strip()
        auth_token = str(data.get("auth") or self.get_argument("auth", "")).strip()
        user_agent_header = self.request.headers.get("User-Agent", "Background GPS Tracker Service")

        if client_uuid:
            is_auth, reason, dev_info = FleetTrackingService.verify_or_bind_device(
                team_code=team_code,
                site_id=site_id,
                device_id=client_uuid,
                user_agent=user_agent_header,
                auth_token=auth_token
            )
            if not is_auth:
                self.set_status(403)
                self.write(json.dumps({
                    "success": False,
                    "access_denied": True,
                    "reason": reason,
                    "lead_name": dev_info.get("lead_name"),
                    "phone": dev_info.get("phone"),
                    "message": dev_info.get("message", "ACCESS DENIED: Unauthorized device. This link is locked to assigned Lead PIC phone.")
                }))
                return

        status = str(data.get("status") or self.get_argument("status", "Confirmed - En Route")).strip()
        notes = str(data.get("notes") or self.get_argument("notes", "")).strip()

        try:
            lat = float(data.get("lat") or self.get_argument("lat"))
            lon = float(data.get("lon") or self.get_argument("lon"))
            accuracy_m = float(data.get("accuracy_m") or data.get("accuracy") or self.get_argument("accuracy_m", self.get_argument("accuracy", 10.0)))
        except (TypeError, ValueError, tornado.web.MissingArgumentError):
            self.set_status(400)
            self.write(json.dumps({
                "success": False,
                "error": "Invalid or missing latitude/longitude coordinates. Example: /api/checkin?id=TEAM-MW017&lat=-6.9228&lon=107.7118"
            }))
            return

        user_agent_header = self.request.headers.get("User-Agent", "Background GPS Tracker Service")

        # Record check-in in SQLite database
        ok, msg = FleetTrackingService.record_team_checkin(
            team_code=team_code,
            site_id=site_id,
            lat=lat,
            lon=lon,
            status=status,
            accuracy_m=accuracy_m,
            user_agent=user_agent_header,
            notes=notes or ("Traccar / Background GPS Tracking Ping" if "Traccar" in user_agent_header else "Continuous live GPS telemetry")
        )

        # Lookup site for geofence calculation
        cleaned_site_id = site_id.replace("-", "").upper()
        df_site = query_df(
            "SELECT site_id, site_name, district, lat, lon, accessible_route_km, operator "
            "FROM timor_sites_100 WHERE UPPER(site_id) = ? OR UPPER(REPLACE(site_id, '-', '')) = ? LIMIT 1",
            (site_id, cleaned_site_id)
        )
        if df_site.empty:
            df_site = query_df("SELECT site_id, site_name, district, lat, lon, accessible_route_km, operator FROM timor_sites_100 LIMIT 1")

        site_row = df_site.iloc[0] if not df_site.empty else {}
        site_lat = float(site_row.get("lat", -8.5621))
        site_lon = float(site_row.get("lon", 125.5382))
        accessible_route_km = float(site_row.get("accessible_route_km") or 15.0)

        geo = FleetTrackingService.calculate_geofence_status(
            team_lat=lat,
            team_lon=lon,
            site_lat=site_lat,
            site_lon=site_lon,
            checkin_status=status,
            accessible_route_km=accessible_route_km
        )

        address = FleetTrackingService.reverse_geocode(lat, lon)
        self.write(json.dumps({
            "success": ok,
            "message": msg,
            "team_code": team_code,
            "site_id": site_id,
            "lat": lat,
            "lon": lon,
            "address": address,
            "dist_km": geo.get("dist_km"),
            "road_dist_km": geo.get("road_dist_km", geo.get("dist_km")),
            "air_dist_km": geo.get("air_dist_km", geo.get("dist_km")),
            "eta_to_site": geo.get("eta_to_site", "Standby"),
            "duration_minutes": geo.get("duration_minutes"),
            "is_out_of_area": geo.get("is_out_of_area", False),
            "flag_label": geo.get("flag_label", "IN CORRIDOR"),
            "flag_type": geo.get("flag_type", "IN_CORRIDOR"),
            "badge_bg": geo.get("badge_bg"),
            "badge_fg": geo.get("badge_fg")
        }))


class MobileCheckinPageHandler(_RequestHandler):
    """
    Renders a lightning-fast, native HTML5 mobile page for field crews.
    No iframe, no heavy Streamlit bundle, 100% reliable 1-tap GPS permission.
    """
    def get(self):
        team_code = self.get_argument("checkin", self.get_argument("team", "TEAM-MW111")).strip().upper()
        site_id = self.get_argument("site", "DAX001").strip().upper()
        auth_token = self.get_argument("auth", "").strip()

        # Query team details
        df_team = query_df("SELECT * FROM paas_field_teams WHERE team_code = ?", (team_code,))
        if not df_team.empty:
            team = df_team.iloc[0].to_dict()
        else:
            team = {
                "team_code": team_code,
                "team_name": f"Field Crew {team_code}",
                "lead_name": "Field Lead PIC",
                "contact_number": "-",
                "crew_size": 4
            }

        # Format masked phone
        raw_phone = str(team.get("contact_number") or "-")
        raw_digits = "".join(c for c in raw_phone if c.isdigit())
        if len(raw_digits) >= 8:
            masked_phone = f"+{raw_digits[:2]} {raw_digits[2:5]}-••••-{raw_digits[-4:]}"
        else:
            masked_phone = raw_phone

        # Query site details
        cleaned_site_id = site_id.replace("-", "").upper()
        df_site = query_df(
            "SELECT * FROM timor_sites_100 WHERE UPPER(site_id) = ? OR UPPER(REPLACE(site_id, '-', '')) = ? LIMIT 1",
            (site_id, cleaned_site_id)
        )
        if df_site.empty:
            df_site = query_df("SELECT * FROM timor_sites_100 LIMIT 1")

        site = df_site.iloc[0].to_dict() if not df_site.empty else {
            "site_id": site_id,
            "site_name": "Target Tower Site",
            "district": "Main District",
            "operator": "National Operator",
            "rectifier": "Eltek 48V/3000W",
            "accessible_route_km": 15.0,
            "transport_mode": "4x4 Overland",
            "est_travel_time": "1h 30m"
        }

        html = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Samvad Field Dispatch // {team['team_code']}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #F1F5F9;
            color: #0F172A;
            padding: 16px;
            line-height: 1.45;
            -webkit-font-smoothing: antialiased;
        }}
        .container {{
            max-width: 480px;
            margin: 0 auto;
        }}
        .header-card {{
            background: #0F172A;
            border-radius: 10px;
            padding: 18px 20px;
            color: #FFFFFF;
            margin-bottom: 14px;
            box-shadow: 0 4px 12px rgba(15,23,42,0.15);
        }}
        .badge-sub {{
            font-size: 0.70rem;
            font-weight: 800;
            color: #38BDF8;
            letter-spacing: 1px;
            text-transform: uppercase;
            display: inline-block;
            margin-bottom: 4px;
        }}
        .title {{
            font-size: 1.25rem;
            font-weight: 800;
            letter-spacing: -0.3px;
        }}
        .lead-info {{
            font-size: 0.82rem;
            color: #94A3B8;
            margin-top: 6px;
        }}
        .lead-info b {{ color: #F8FAFC; }}
        .card {{
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 16px 18px;
            margin-bottom: 14px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }}
        .card-title {{
            font-size: 0.76rem;
            font-weight: 800;
            color: #475569;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
            padding-bottom: 6px;
            border-bottom: 1px solid #F1F5F9;
        }}
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            font-size: 0.82rem;
        }}
        .grid-label {{
            color: #64748B;
            font-size: 0.72rem;
            display: block;
            margin-bottom: 2px;
        }}
        .grid-val {{
            font-weight: 700;
            color: #0F172A;
        }}
        .btn-action {{
            display: block;
            width: 100%;
            background: #0284C7;
            color: #FFFFFF;
            font-weight: 800;
            font-size: 0.95rem;
            padding: 16px 18px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            letter-spacing: 0.3px;
            text-transform: uppercase;
            text-align: center;
            box-shadow: 0 3px 6px rgba(2, 132, 199, 0.3);
            transition: all 0.15s ease;
        }}
        .btn-action:active {{
            transform: scale(0.98);
        }}
        .btn-action:disabled {{
            opacity: 0.75;
            cursor: wait;
        }}
        .btn-secondary {{
            display: block;
            width: 100%;
            background: #F1F5F9;
            color: #334155;
            font-weight: 700;
            font-size: 0.82rem;
            padding: 10px 14px;
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            cursor: pointer;
            text-align: center;
            margin-top: 8px;
        }}
        .status-select {{
            width: 100%;
            padding: 11px 12px;
            font-size: 0.88rem;
            font-weight: 700;
            border-radius: 6px;
            border: 1.5px solid #CBD5E1;
            background: #FFFFFF;
            color: #0F172A;
            margin-bottom: 12px;
            outline: none;
        }}
        .result-box {{
            display: none;
            background: #F0FDF4;
            border: 1.5px solid #22C55E;
            border-left: 6px solid #16A34A;
            border-radius: 8px;
            padding: 14px 16px;
            margin-top: 14px;
        }}
        .result-title {{
            font-weight: 800;
            font-size: 0.90rem;
            color: #15803D;
            margin-bottom: 4px;
        }}
        .result-desc {{
            font-size: 0.80rem;
            color: #166534;
            line-height: 1.5;
        }}
        .badge-geo {{
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 4px;
            margin-top: 6px;
        }}
        .error-box {{
            display: none;
            background: #FEF2F2;
            border: 1px solid #FECACA;
            border-left: 5px solid #DC2626;
            border-radius: 8px;
            padding: 12px 14px;
            font-size: 0.80rem;
            color: #B91C1C;
            margin-top: 12px;
        }}
        .input-text {{
            width: 100%;
            padding: 10px 12px;
            font-size: 0.82rem;
            border: 1.5px solid #CBD5E1;
            border-radius: 6px;
            margin-bottom: 8px;
            outline: none;
        }}
        @keyframes beacon-glow {{
            0% {{ opacity: 0.35; transform: scale(0.95); }}
            50% {{ opacity: 1; transform: scale(1.15); }}
            100% {{ opacity: 0.35; transform: scale(0.95); }}
        }}
        .beacon-pill {{
            display: inline-flex;
            align-items: center;
            background: #ECFDF5;
            color: #15803D;
            font-weight: 800;
            font-size: 0.72rem;
            padding: 4px 10px;
            border-radius: 9999px;
            border: 1px solid #86EFAC;
            margin-bottom: 6px;
        }}
        .beacon-dot {{
            width: 8px;
            height: 8px;
            background: #16A34A;
            border-radius: 50%;
            margin-right: 6px;
            animation: beacon-glow 1.5s infinite;
        }}
        .live-status-box {{
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 10px 12px;
            margin-top: 10px;
            font-size: 0.76rem;
            color: #334155;
            line-height: 1.5;
        }}
        .btn-stop {{
            background: #FFFFFF;
            color: #DC2626;
            border: 1.5px solid #FCA5A5;
            padding: 9px 12px;
            font-size: 0.75rem;
            font-weight: 700;
            border-radius: 6px;
            cursor: pointer;
            margin-top: 10px;
            width: 100%;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header Card -->
        <div class="header-card">
            <span class="badge-sub">SAMVAD PMO-CC // FIELD DISPATCH</span>
            <div class="title">Confirmation &amp; Live GPS Telemetry</div>
            <div class="lead-info">
                Field Lead PIC: <b>{team['lead_name']}</b> ({team['team_code']}) &bull; PIC Contact: <b>{masked_phone}</b>
            </div>
        </div>

        <!-- Security & Device Binding Banner -->
        <div style="background: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 8px; padding: 10px 14px; margin-bottom: 14px;">
            <div style="font-size: 0.74rem; font-weight: 800; color: #0284C7; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px;">
                SECURITY: 1-DEVICE ASSIGNMENT LOCK
            </div>
            <div style="font-size: 0.72rem; color: #334155; line-height: 1.45;">
                Link tracking ini diotorisasi khusus untuk Lead PIC: <b>{team['lead_name']}</b> ({masked_phone}).
                Perangkat pertama yang mengaktifkan tracking akan dikunci sebagai perangkat resmi. Membagikan link ini ke perangkat lain akan otomatis <b>diblokir</b> oleh sistem untuk mencegah bentrokan lokasi GPS.
            </div>
        </div>

        <!-- Access Denied Alert Box -->
        <div id="access-denied-box" style="display: none; background: #FEF2F2; border: 2px solid #DC2626; border-radius: 8px; padding: 16px; margin-bottom: 14px;">
            <div style="font-weight: 800; font-size: 0.90rem; color: #991B1B; margin-bottom: 6px; text-transform: uppercase;">
                AKSES DITOLAK (ACCESS DENIED)
            </div>
            <div id="access-denied-desc" style="font-size: 0.80rem; color: #B91C1C; line-height: 1.5; margin-bottom: 10px;">
                Perangkat ini tidak diotorisasi untuk assignment tim {team['team_code']}.
            </div>
            <div style="font-size: 0.73rem; color: #7F1D1D; background: #FEE2E2; padding: 8px 10px; border-radius: 6px; line-height: 1.4;">
                Link tugas ini telah terkunci pada perangkat smartphone PIC terdaftar ({masked_phone}). Untuk mengganti perangkat resmi, hubungi PMO Controller agar dilakukan reset device binding.
            </div>
        </div>

        <!-- Scope Card -->
        <div class="card">
            <div class="card-title">TOWER SITE ASSIGNMENT</div>
            <div class="grid-2">
                <div>
                    <span class="grid-label">Target Site:</span>
                    <span class="grid-val">{site['site_id']} — {site['site_name']}</span>
                </div>
                <div>
                    <span class="grid-label">Region &amp; Operator:</span>
                    <span class="grid-val">{site['district']} ({site['operator']})</span>
                </div>
                <div>
                    <span class="grid-label">Site GPS Coordinates:</span>
                    <span class="grid-val">{site.get('lat', -8.5621):.5f}, {site.get('lon', 125.5382):.5f}</span>
                </div>
                <div>
                    <span class="grid-label">Route &amp; Transport:</span>
                    <span class="grid-val">{site['transport_mode']} &bull; {site['est_travel_time']}</span>
                </div>
            </div>
        </div>

        <!-- 1-Tap Action Card -->
        <div class="card">
            <div class="card-title">SHARE SMARTPHONE GPS LOCATION</div>
            <div style="font-size: 0.78rem; color: #475569; margin-bottom: 12px; line-height: 1.5;">
                Select your work status. Live GPS telemetry broadcasts automatically every 20 seconds to the PMO Command Center Radar.
            </div>

            <label for="sel-status" style="font-size: 0.72rem; font-weight: 800; color: #475569; display: block; margin-bottom: 4px; text-transform: uppercase;">
                Work Status:
            </label>
            <select id="sel-status" class="status-select">
                <option value="Confirmed - En Route" selected>Confirmed - En Route (Traveling to Site)</option>
                <option value="On-Site Active (WIP)">On-Site Active (Working on Site)</option>
                <option value="Task Completed / Ready for ATP">Task Completed (Ready for ATP)</option>
                <option value="Standby / Awaiting Material">Standby (Awaiting Material)</option>
            </select>

            <!-- Controller Enforced Telemetry Banner -->
            <div style="background: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 6px; padding: 10px 12px; margin-bottom: 12px;">
                <div style="font-size: 0.76rem; color: #0F172A; font-weight: 800; text-transform: uppercase; margin-bottom: 2px;">
                    Continuous Background Telemetry: Enforced by PMO Controller
                </div>
                <div style="font-size: 0.72rem; color: #64748B; line-height: 1.4;">
                    GPS coordinates broadcast automatically while traveling. This tracking session is actively monitored and terminated exclusively by the PMO Controller.
                </div>
                <input type="hidden" id="chk-continuous" value="1">
            </div>

            <button id="btn-share" class="btn-action" onclick="transmitGps()">
                CLICK TO START LIVE TRACKING
            </button>

            <!-- Success Box -->
            <div id="result-box" class="result-box">
                <div class="beacon-pill" id="live-indicator">
                    <span class="beacon-dot"></span>
                    <span id="beacon-status-text">LIVE BEACON ACTIVE &bull; BROADCASTING LOCATION</span>
                </div>
                <div class="result-title">LOCATION RECEIVED BY PMO COMMAND CENTER RADAR</div>
                <div id="result-desc" class="result-desc"></div>
                <div id="result-badge" class="badge-geo"></div>
                <div class="live-status-box" id="live-status-box">
                    <div style="font-weight: 800; color: #0F172A; margin-bottom: 3px;" id="live-ping-count">
                        Transmission: Ping #1 Sent Successfully
                    </div>
                    <div id="live-telemetry-metrics" style="font-size: 0.74rem; color: #0284C7; font-weight: 700; margin-bottom: 4px;"></div>
                    <div id="live-timer-text" style="font-size: 0.73rem; color: #64748B;">
                        Automatic Background Tracking Active &bull; Managed exclusively by PMO Controller.
                    </div>
                </div>
            </div>

            <!-- Error Box -->
            <div id="error-box" class="error-box"></div>
        </div>

        <!-- Backup Option: Paste WhatsApp Pin -->
        <div class="card" style="border-style: dashed;">
            <div class="card-title">OR PASTE WHATSAPP LOCATION PIN</div>
            <div style="font-size: 0.76rem; color: #64748B; margin-bottom: 8px;">
                If browser GPS cannot be accessed, share your location via WhatsApp, then copy and paste the link or coordinates here:
            </div>
            <input type="text" id="manual-pin" class="input-text" placeholder="e.g. -6.23081, 106.81581 or Google Maps link">
            <button class="btn-secondary" onclick="transmitManualPin()">
                TRANSMIT PIN TO RADAR
            </button>
        </div>
        <audio id="bg-audio" src="/silence.wav" loop playsinline preload="auto" style="display:none;"></audio>
    </div>

    <script>
    const teamCode = "{team['team_code']}";
    const siteId = "{site['site_id']}";
    const authToken = "{auth_token}";

    // Retrieve or generate persistent hardware/device UUID for 1-Device Binding
    let clientUuid = '';
    try {{
        clientUuid = localStorage.getItem('samvad_device_uuid');
        if (!clientUuid) {{
            clientUuid = 'dev_' + Math.random().toString(36).substring(2, 10) + '_' + Date.now().toString(36);
            localStorage.setItem('samvad_device_uuid', clientUuid);
        }}
    }} catch(e) {{
        clientUuid = 'dev_tmp_' + Date.now().toString(36);
    }}

    let isTrackingActive = false;
    let watchdogTimer = null;
    let watchId = null;
    let pingCount = 0;
    let wakeLockObj = null;
    let lastSentTime = 0;
    let lastSentLat = null;
    let lastSentLon = null;
    let lastSentAcc = null;
    let bgAudio = null;

    async function requestWakeLock() {{
        if ('wakeLock' in navigator) {{
            try {{
                wakeLockObj = await navigator.wakeLock.request('screen');
                if (wakeLockObj) {{
                    wakeLockObj.addEventListener('release', function() {{}});
                }}
            }} catch(e) {{}}
        }}
    }}

    let audioCtx = null;

    function unlockAudioSynchronously() {{
        try {{
            const AC = window.AudioContext || window.webkitAudioContext;
            if (AC && !audioCtx) {{
                audioCtx = new AC();
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                gain.gain.value = 0.0001;
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start(0);
            }}
            if (audioCtx && audioCtx.state === 'suspended') {{
                audioCtx.resume();
            }}
        }} catch(e) {{}}
        try {{
            if (!bgAudio) {{
                bgAudio = document.getElementById('bg-audio');
            }}
            if (bgAudio) {{
                bgAudio.volume = 0.01;
                const p = bgAudio.play();
                if (p && p.catch) {{
                    p.catch(function() {{}});
                }}
            }}
            if ('mediaSession' in navigator) {{
                navigator.mediaSession.metadata = new MediaMetadata({{
                    title: "Samvad Field Telemetry Active",
                    artist: teamCode + " (Continuous Tracking)",
                    album: "PMO Command Center Radar"
                }});
                navigator.mediaSession.playbackState = 'playing';
            }}
        }} catch(e) {{}}
    }}

    function calcDistMeters(lat1, lon1, lat2, lon2) {{
        const R = 6371000;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    }}

    let offlineQueue = [];
    try {{
        const savedQueue = localStorage.getItem('samvad_offline_' + teamCode);
        if (savedQueue) offlineQueue = JSON.parse(savedQueue);
    }} catch(e) {{}}

    function saveOfflinePoint(pLat, pLon, pAcc, pStat) {{
        if (offlineQueue.length >= 250) offlineQueue.shift();
        offlineQueue.push({{
            team_code: teamCode,
            site_id: siteId,
            lat: parseFloat(pLat),
            lon: parseFloat(pLon),
            accuracy_m: parseFloat(pAcc || 10.0),
            status: pStat
        }});
        try {{
            localStorage.setItem('samvad_offline_' + teamCode, JSON.stringify(offlineQueue));
        }} catch(e) {{}}
    }}

    function flushOfflineQueue() {{
        if (!offlineQueue || offlineQueue.length === 0) return;
        const chunk = offlineQueue.slice(0, 25);
        fetch('/api/checkin', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ batch: chunk, client_uuid: clientUuid, auth: authToken }})
        }})
        .then(function(res) {{ return res.json(); }})
        .then(function(resData) {{
            if (resData.success) {{
                offlineQueue.splice(0, chunk.length);
                try {{
                    localStorage.setItem('samvad_offline_' + teamCode, JSON.stringify(offlineQueue));
                }} catch(e) {{}}
                if (offlineQueue.length > 0) {{
                    setTimeout(flushOfflineQueue, 1500);
                }}
            }}
        }})
        .catch(function() {{}});
    }}

    function startHardwareGpsWatch(status) {{
        if (!navigator.geolocation) return;
        if (watchId !== null) {{
            try {{ navigator.geolocation.clearWatch(watchId); }} catch(e) {{}}
            watchId = null;
        }}

        try {{
            watchId = navigator.geolocation.watchPosition(
                function(pos) {{
                    if (!isTrackingActive) return;
                    const now = Date.now();
                    const lat = pos.coords.latitude;
                    const lon = pos.coords.longitude;
                    const acc = pos.coords.accuracy || 10.0;
                    const spdKmh = (pos.coords.speed && pos.coords.speed > 0) ? (pos.coords.speed * 3.6).toFixed(1) : "0.0";

                    // Update live on-screen metrics immediately
                    const metricsEl = document.getElementById('live-telemetry-metrics');
                    if (metricsEl) {{
                        const isMoving = parseFloat(spdKmh) > 2.0;
                        const moveState = isMoving ? "BERGERAK (" + spdKmh + " km/jam)" : "STANDBY (Diam)";
                        metricsEl.innerHTML = "GPS: <b>" + lat.toFixed(5) + ", " + lon.toFixed(5) + "</b> (&plusmn;" + Math.round(acc) + "m) &bull; Status: <b>" + moveState + "</b>";
                    }}

                    let movedMeters = 999;
                    if (lastSentLat !== null && lastSentLon !== null) {{
                        movedMeters = calcDistMeters(lastSentLat, lastSentLon, lat, lon);
                    }}

                    const elapsedMs = now - lastSentTime;
                    // Transmit to server whenever:
                    // A) First transmission, OR
                    // B) Technician moved >= 5 meters, OR
                    // C) 10 seconds elapsed since last transmission (heartbeat)
                    if (lastSentLat === null || movedMeters >= 5 || elapsedMs >= 10000) {{
                        lastSentTime = now;
                        lastSentLat = lat;
                        lastSentLon = lon;
                        lastSentAcc = acc;
                        sendTelemetry(lat, lon, acc, status, true, true, spdKmh);
                    }}
                }},
                function(err) {{
                    // Temporary signal fluctuation; do not kill watch
                }},
                {{ enableHighAccuracy: true, maximumAge: 0, timeout: 15000 }}
            );
        }} catch(e) {{}}
    }}

    let bgWorker = null;

    function startWatchdogHeartbeat() {{
        if (watchdogTimer || bgWorker) return;
        try {{
            const blob = new Blob([
                "let t = null;" +
                "self.onmessage = function(e) {{" +
                "  if (e.data === 'start') {{" +
                "    if (t) clearInterval(t);" +
                "    t = setInterval(function() {{ self.postMessage('tick'); }}, 10000);" +
                "  }} else if (e.data === 'stop') {{" +
                "    if (t) clearInterval(t);" +
                "    t = null;" +
                "  }}" +
                "}};"
            ], {{ type: 'application/javascript' }});
            bgWorker = new Worker(URL.createObjectURL(blob));
            bgWorker.onmessage = function(e) {{
                if (e.data === 'tick' && isTrackingActive) {{
                    onHeartbeatTick();
                }}
            }};
            bgWorker.postMessage('start');
        }} catch(e) {{
            watchdogTimer = setInterval(function() {{
                if (isTrackingActive) onHeartbeatTick();
            }}, 10000);
        }}
    }}

    function onHeartbeatTick() {{
        if (!isTrackingActive) return;
        const now = Date.now();
        const elapsed = now - lastSentTime;
        const selStatus = document.getElementById('sel-status').value;

        // If watchPosition hasn't transmitted in 15 seconds, send heartbeat
        if (elapsed >= 15000) {{
            if (lastSentLat !== null && lastSentLon !== null) {{
                lastSentTime = now;
                sendTelemetry(lastSentLat, lastSentLon, lastSentAcc || 10.0, selStatus, true, true, "0.0");
            }} else {{
                navigator.geolocation.getCurrentPosition(
                    function(pos) {{
                        lastSentLat = pos.coords.latitude;
                        lastSentLon = pos.coords.longitude;
                        lastSentAcc = pos.coords.accuracy;
                        lastSentTime = Date.now();
                        sendTelemetry(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy, selStatus, true, true, "0.0");
                    }},
                    function(err) {{}},
                    {{ enableHighAccuracy: true, timeout: 8000, maximumAge: 5000 }}
                );
            }}
        }}
    }}

    function transmitGps(isAutoPing = false) {{
        const btn = document.getElementById('btn-share');
        const errBox = document.getElementById('error-box');
        const selStatus = document.getElementById('sel-status').value;

        if (!isAutoPing) {{
            errBox.style.display = 'none';
            btn.disabled = true;
            btn.innerText = "ACCESSING SMARTPHONE GPS SENSOR...";
            btn.style.background = "#0284C7";
        }}

        isTrackingActive = true;
        unlockAudioSynchronously();
        requestWakeLock();

        if (!navigator.geolocation) {{
            showError("Your smartphone browser does not support the Geolocation API. Please use the WhatsApp pin box below.");
            btn.disabled = false;
            return;
        }}

        // Send instant initial fix
        navigator.geolocation.getCurrentPosition(
            function(pos) {{
                lastSentLat = pos.coords.latitude;
                lastSentLon = pos.coords.longitude;
                lastSentAcc = pos.coords.accuracy;
                lastSentTime = Date.now();
                sendTelemetry(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy, selStatus, true, isAutoPing, "0.0");
                startHardwareGpsWatch(selStatus);
                startWatchdogHeartbeat();
            }},
            function(err) {{
                startHardwareGpsWatch(selStatus);
                startWatchdogHeartbeat();
                if (!isAutoPing) handleGpsError(err);
            }},
            {{ enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }}
        );
    }}

    function handleGpsError(err) {{
        const btn = document.getElementById('btn-share');
        btn.disabled = false;
        btn.innerText = "CLICK TO START LIVE TRACKING";

        let msg = "Failed to access GPS: ";
        if (err.code === 1) {{
            msg = "Izin lokasi terblokir oleh sistem Android.<br><b>Solusi Cepat:</b> Tutup/geser gelembung melayang aplikasi lain (seperti gelembung Driver/Chat di sisi kanan layar) ke bawah layar, lalu klik tombol untuk mengizinkan lokasi.";
        }} else if (err.code === 2) {{
            msg = "Device GPS signal unavailable. Please ensure Location/GPS is turned on in your phone settings.";
        }} else if (err.code === 3) {{
            msg = "GPS acquisition timeout. Please click the button to retry.";
        }} else {{
            msg += err.message;
        }}
        showError(msg);
    }}

    function showError(msg) {{
        const errBox = document.getElementById('error-box');
        errBox.innerHTML = "<b>Notice:</b> " + msg;
        errBox.style.display = 'block';
    }}

    function handleAccessDenied(msg) {{
        stopContinuousTracking();
        const accessBox = document.getElementById('access-denied-box');
        const accessDesc = document.getElementById('access-denied-desc');
        const btn = document.getElementById('btn-share');
        if (accessDesc) accessDesc.innerText = msg;
        if (accessBox) accessBox.style.display = 'block';
        if (btn) {{
            btn.disabled = true;
            btn.innerText = "ACCESS DENIED (DEVICE MISMATCH)";
            btn.style.background = "#DC2626";
        }}
        showError("Security Alert: Device not authorized for this assignment.");
    }}

    function sendTelemetry(lat, lon, acc, status, isContinuous, isAutoPing, speedKmh) {{
        const btn = document.getElementById('btn-share');
        if (!isAutoPing) btn.innerText = "TRANSMITTING TO PMO RADAR...";

        fetch('/api/checkin', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
                team_code: teamCode,
                site_id: siteId,
                client_uuid: clientUuid,
                auth: authToken,
                lat: parseFloat(lat),
                lon: parseFloat(lon),
                accuracy_m: parseFloat(acc || 10.0),
                status: status,
                speed_kmh: speedKmh || "0.0"
            }})
        }})
        .then(function(res) {{
            if (res.status === 403) {{
                return res.json().then(function(errData) {{
                    throw {{ isAccessDenied: true, data: errData }};
                }});
            }}
            return res.json();
        }})
        .then(function(data) {{
            if (data.access_denied) {{
                handleAccessDenied(data.message);
                return;
            }}
            if (data.controller_terminated || data.tracking_active === false) {{
                stopContinuousTracking();
                const resBox = document.getElementById('result-box');
                const pingCountEl = document.getElementById('live-ping-count');
                const timerText = document.getElementById('live-timer-text');
                const beaconPill = document.getElementById('live-indicator');
                if (pingCountEl) pingCountEl.innerHTML = "<span style='color: #059669; font-weight: 800;'>ASSIGNMENT CLOSED BY PMO CONTROLLER</span>";
                if (timerText) timerText.innerHTML = "PMO Controller has formally terminated this tracking session. Background GPS tracking is now completely turned off. You may now close this browser tab.";
                if (beaconPill) beaconPill.style.display = 'none';
                btn.disabled = true;
                btn.innerText = "SESSION CONCLUDED BY PMO CONTROLLER";
                btn.style.background = "#64748B";
                if (resBox) resBox.style.display = 'block';
                return;
            }}

            pingCount++;
            btn.disabled = false;

            const resBox = document.getElementById('result-box');
            const resDesc = document.getElementById('result-desc');
            const resBadge = document.getElementById('result-badge');
            const pingCountEl = document.getElementById('live-ping-count');
            const liveBox = document.getElementById('live-status-box');
            const timerText = document.getElementById('live-timer-text');
            const metricsEl = document.getElementById('live-telemetry-metrics');

            const now = new Date();
            const timeStr = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0') + ':' + String(now.getSeconds()).padStart(2, '0');

            const addrHtml = data.address ? "Address: <b>" + data.address + "</b>.<br>" : "";
            const distHtml = (data.road_dist_km !== undefined && data.road_dist_km !== null)
                ? "Road Distance to Site: <b>" + data.road_dist_km.toFixed(1) + " km</b> (ETA: <b>" + (data.eta_to_site || "-") + "</b> via Fastest Road).<br>"
                : (data.dist_km ? "Distance to Tower Site: <b>" + data.dist_km.toFixed(1) + " km</b>.<br>" : "");
            resDesc.innerHTML = "Team <b>" + teamCode + "</b> actively transmitted to PMO Radar.<br>" +
                                "GPS Coordinates: <b>" + lat.toFixed(5) + ", " + lon.toFixed(5) + "</b> (Accuracy: " + Math.round(acc) + "m).<br>" +
                                addrHtml +
                                distHtml +
                                "Last Transmitted: <b>" + timeStr + " WIB</b>.";

            resBadge.innerText = data.flag_label || (data.is_out_of_area ? "FLAG: OUT OF AREA" : "IN CORRIDOR");
            resBadge.style.background = data.badge_bg || (data.is_out_of_area ? "#FEF2F2" : "#EFF6FF");
            resBadge.style.color = data.badge_fg || (data.is_out_of_area ? "#DC2626" : "#0284C7");
            resBadge.style.border = "1px solid " + (data.is_out_of_area ? "#FECACA" : "#BFDBFE");

            if (status === "Task Completed / Ready for ATP") {{
                btn.style.background = "#059669";
                btn.innerText = "STATUS TRANSMITTED: READY FOR ATP";
                liveBox.style.display = 'block';
                if (pingCountEl) pingCountEl.innerHTML = "Task Status: <b>READY FOR ATP (Transmitted to Radar)</b> (" + timeStr + ")";
                if (timerText) timerText.innerHTML = "Status received by Command Center. Telemetry stands by until verified by PMO Controller.";
            }} else {{
                btn.style.background = "#15803D";
                btn.innerText = "LIVE GPS TELEMETRY ACTIVE (AUTOPING 12s)";
                liveBox.style.display = 'block';
                if (pingCountEl) pingCountEl.innerHTML = "Transmission: <b>Ping #" + pingCount + " Successfully Sent to Radar</b> (" + timeStr + ")";
                if (timerText) timerText.innerHTML = "Screen WakeLock Active &bull; Managed exclusively by PMO Controller. Keep screen on in holder while driving.";
            }}

            if (metricsEl) {{
                const spdVal = parseFloat(speedKmh || "0");
                const moveState = spdVal > 2.0 ? "BERGERAK (" + spdVal.toFixed(1) + " km/jam)" : "STANDBY (Diam)";
                metricsEl.innerHTML = "GPS: <b>" + lat.toFixed(5) + ", " + lon.toFixed(5) + "</b> (&plusmn;" + Math.round(acc) + "m) &bull; Status: <b>" + moveState + "</b>";
            }}

            resBox.style.display = 'block';
            flushOfflineQueue();
        }})
        .catch(function(err) {{
            if (err && err.isAccessDenied) {{
                handleAccessDenied(err.data ? err.data.message : "Access Denied: Unauthorized device.");
                return;
            }}
            saveOfflinePoint(lat, lon, acc, status);
            if (!isAutoPing) {{
                btn.disabled = false;
                btn.innerText = "CACHED LOCALLY (OFFLINE - RETRYING)";
                btn.style.background = "#D97706";
                showError("Connection temporarily interrupted. Coordinates saved on device and broadcasting continuously. Will auto-sync to Command Center once reconnected.");
            }}
        }});
    }}

    function stopContinuousTracking() {{
        isTrackingActive = false;
        if (bgWorker) {{
            try {{ bgWorker.postMessage('stop'); bgWorker.terminate(); }} catch(e) {{}}
            bgWorker = null;
        }}
        if (watchdogTimer) {{
            clearInterval(watchdogTimer);
            watchdogTimer = null;
        }}
        if (watchId !== null && navigator.geolocation) {{
            try {{ navigator.geolocation.clearWatch(watchId); }} catch(e) {{}}
            watchId = null;
        }}
        if (wakeLockObj) {{
            try {{ wakeLockObj.release(); }} catch(e) {{}}
            wakeLockObj = null;
        }}
        if (audioCtx) {{
            try {{ audioCtx.suspend(); }} catch(e) {{}}
        }}
        if (bgAudio) {{
            try {{ bgAudio.pause(); }} catch(e) {{}}
        }}
        const pingCountEl = document.getElementById('live-ping-count');
        const timerText = document.getElementById('live-timer-text');
        const beaconPill = document.getElementById('live-indicator');
        const btn = document.getElementById('btn-share');

        if (pingCountEl) pingCountEl.innerText = "Automatic Background Tracking Paused";
        if (timerText) timerText.innerText = "Periodic transmissions paused. Click the button above to resume.";
        if (beaconPill) beaconPill.style.display = 'none';
        btn.disabled = false;
        btn.innerText = "RESUME LIVE TRACKING";
        btn.style.background = "#0284C7";
    }}

    // Check persistent permission on load
    if (navigator.permissions && navigator.permissions.query) {{
        navigator.permissions.query({{ name: 'geolocation' }}).then(function(result) {{
            if (result.state === 'granted') {{
                setTimeout(function() {{ transmitGps(false); }}, 400);
            }}
            result.onchange = function() {{
                if (result.state === 'granted') {{
                    setTimeout(function() {{ transmitGps(false); }}, 400);
                }}
            }};
        }}).catch(function() {{}});
    }}

    // Visibility change listener to restore WakeLock and resume tracking when screen is turned back on
    document.addEventListener('visibilitychange', function() {{
        if (document.visibilityState === 'visible') {{
            unlockAudioSynchronously();
            if (isTrackingActive) {{
                requestWakeLock();
                if (watchId === null) {{
                    startHardwareGpsWatch(document.getElementById('sel-status').value);
                }}
            }}
            flushOfflineQueue();
        }}
    }});

    function transmitManualPin() {{
        const text = document.getElementById('manual-pin').value.trim();
        const selStatus = document.getElementById('sel-status').value;
        if (!text) {{
            showError("Please enter or paste coordinates / Maps link.");
            return;
        }}
        const match = text.match(/(?:q=|@|loc:)?(-?\\d{{1,2}}\\.\\d+)[,\\s]+(-?\\d{{1,3}}\\.\\d+)/);
        if (match) {{
            const pLat = parseFloat(match[1]);
            const pLon = parseFloat(match[2]);
            sendTelemetry(pLat, pLon, 5.0, selStatus, false, false, "0.0");
        }} else {{
            showError("Unrecognized coordinate format. Valid example: -6.23081, 106.81581");
        }}
    }}
    </script>
</body>
</html>
"""
        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.write(html)


def attach_mobile_checkin_routes() -> bool:
    """
    Finds running Tornado application instances in memory and prepends
    the mobile check-in portal and JSON API routes before Streamlit's fallback handler.
    """
    if not HAS_TORNADO or tornado is None:
        return False
    attached = False
    for obj in gc.get_objects():
        if isinstance(obj, tornado.web.Application):
            if not getattr(obj, "_samvad_mobile_routes_attached", False):
                try:
                    obj.wildcard_router.rules.insert(0, Rule(PathMatches(r"/silence\.wav"), SilenceAudioHandler))
                    obj.wildcard_router.rules.insert(0, Rule(PathMatches(r"/api/checkin"), CheckinApiHandler))
                    obj.wildcard_router.rules.insert(0, Rule(MobileMatcher(), MobileCheckinPageHandler))
                    setattr(obj, "_samvad_mobile_routes_attached", True)
                    attached = True
                except Exception:
                    pass
    return attached
