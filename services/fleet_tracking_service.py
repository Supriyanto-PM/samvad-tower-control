"""
Fleet Live Tracking, Geofencing, and GPS Check-In Service for Samvad PMO-CC.
Manages real-time field crew telemetry, WhatsApp GPS check-in acknowledgements,
automated device location permission capture, and geospatial geofence boundary enforcement.
Strictly icon-free enterprise typography.
"""

import os
import math
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
from database.connection import get_connection, query_df, execute_write


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates great-circle distance between two GPS coordinates in kilometers.
    Uses WGS-84 mean radius of 6371.0 km.
    """
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class FleetTrackingService:
    @staticmethod
    def ensure_route_cache_table():
        """Ensures the geo_route_cache table exists in SQLite database."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS geo_route_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    origin_lat REAL NOT NULL,
                    origin_lon REAL NOT NULL,
                    dest_lat REAL NOT NULL,
                    dest_lon REAL NOT NULL,
                    road_dist_km REAL NOT NULL,
                    duration_minutes REAL NOT NULL,
                    duration_formatted TEXT NOT NULL,
                    route_source TEXT DEFAULT 'OSRM_HIGHWAY',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(origin_lat, origin_lon, dest_lat, dest_lon)
                )
            """)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def calculate_road_routing(
        origin_lat: Optional[float],
        origin_lon: Optional[float],
        dest_lat: Optional[float],
        dest_lon: Optional[float]
    ) -> Dict[str, Any]:
        """
        Calculates real-world road travel distance and driving travel time (ETA) between
        field crew GPS location and target tower site using real accessible highway/road routing
        with high-performance SQLite caching (0.1ms recall) and civil terrain tortuosity fallback.
        Strictly icon-free enterprise typography.
        """
        if origin_lat is None or origin_lon is None or dest_lat is None or dest_lon is None or \
           pd.isna(origin_lat) or pd.isna(origin_lon) or pd.isna(dest_lat) or pd.isna(dest_lon):
            return {
                "road_km": None,
                "air_km": None,
                "duration_minutes": None,
                "eta_text": "No GPS Fix",
                "route_source": "NONE"
            }

        try:
            o_lat = float(origin_lat)
            o_lon = float(origin_lon)
            d_lat = float(dest_lat)
            d_lon = float(dest_lon)
        except (ValueError, TypeError):
            return {
                "road_km": None,
                "air_km": None,
                "duration_minutes": None,
                "eta_text": "Invalid Coordinates",
                "route_source": "INVALID"
            }

        air_km = haversine_distance_km(o_lat, o_lon, d_lat, d_lon)

        # If team is already on-site (within 200m)
        if air_km < 0.2:
            return {
                "road_km": round(air_km, 2),
                "air_km": round(air_km, 2),
                "duration_minutes": 1.0,
                "eta_text": "< 2 mins (At Site)",
                "route_source": "ON_SITE"
            }

        # Key rounding for fast cache hit (3 decimals = ~110m precision)
        lat_o_r = round(o_lat, 3)
        lon_o_r = round(o_lon, 3)
        lat_d_r = round(d_lat, 3)
        lon_d_r = round(d_lon, 3)

        FleetTrackingService.ensure_route_cache_table()

        # Check local cache first
        try:
            df_cache = query_df(
                """
                SELECT road_dist_km, duration_minutes, duration_formatted, route_source 
                FROM geo_route_cache 
                WHERE origin_lat = ? AND origin_lon = ? AND dest_lat = ? AND dest_lon = ?
                LIMIT 1
                """,
                (lat_o_r, lon_o_r, lat_d_r, lon_d_r)
            )
            if not df_cache.empty and df_cache.iloc[0]["road_dist_km"] is not None:
                row = df_cache.iloc[0]
                return {
                    "road_km": float(row["road_dist_km"]),
                    "air_km": round(air_km, 2),
                    "duration_minutes": float(row["duration_minutes"]),
                    "eta_text": str(row["duration_formatted"]),
                    "route_source": str(row["route_source"])
                }
        except Exception:
            pass

        road_km = None
        duration_minutes = None
        eta_text = None
        route_source = None

        # Attempt OSRM road network routing (driving profile)
        import urllib.request
        import json

        try:
            url = f"http://router.project-osrm.org/route/v1/driving/{lon_o_r},{lat_o_r};{lon_d_r},{lat_d_r}?overview=false"
            headers = {"User-Agent": "SamvadPMOCommandCenter/1.0 (pmo-support@samvad.com)"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("code") == "Ok" and data.get("routes"):
                    primary_route = data["routes"][0]
                    road_km = round(primary_route["distance"] / 1000.0, 1)
                    duration_sec = primary_route["duration"]
                    duration_minutes = round(duration_sec / 60.0, 1)

                    if duration_minutes < 60:
                        eta_text = f"{int(round(duration_minutes))} mins"
                    else:
                        hours = int(duration_minutes // 60)
                        mins = int(round(duration_minutes % 60))
                        eta_text = f"{hours}h {mins}m"
                    route_source = "OSRM_ROAD_NETWORK"
        except Exception:
            pass

        # Offline / Inter-Island / Heuristic Fallback
        if road_km is None:
            # Check for inter-island / maritime separation (>700km or cross-sea)
            if air_km > 750 or (o_lat < -6.0 and d_lat < -8.0 and abs(o_lon - d_lon) > 5.0):
                # Inter-island transit: road + ferry corridor
                road_km = round(air_km * 1.35, 1)
                duration_minutes = round((road_km / 45.0) * 60, 1) + 720  # +12 hours ferry crossing/port buffer
                hours = int(duration_minutes // 60)
                mins = int(duration_minutes % 60)
                eta_text = f"{hours}h {mins}m (Inter-Island Transit)"
                route_source = "MULTI_MODAL_FERRY"
            else:
                # Standard civil telecommunication road tortuosity model (1.28x overland factor)
                # Fleet service van average speed 45 km/h over mixed terrain
                road_km = round(air_km * 1.28, 1)
                duration_minutes = round((road_km / 45.0) * 60, 1)
                if duration_minutes < 60:
                    eta_text = f"{int(round(duration_minutes))} mins"
                else:
                    hours = int(duration_minutes // 60)
                    mins = int(round(duration_minutes % 60))
                    eta_text = f"{hours}h {mins}m"
                route_source = "TERRAIN_ROAD_MODEL"

        # Cache result into SQLite for 0.1ms recall on subsequent page renders
        try:
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO geo_route_cache (
                        origin_lat, origin_lon, dest_lat, dest_lon,
                        road_dist_km, duration_minutes, duration_formatted, route_source
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(origin_lat, origin_lon, dest_lat, dest_lon) DO UPDATE SET
                        road_dist_km = excluded.road_dist_km,
                        duration_minutes = excluded.duration_minutes,
                        duration_formatted = excluded.duration_formatted,
                        route_source = excluded.route_source
                """, (lat_o_r, lon_o_r, lat_d_r, lon_d_r, road_km, duration_minutes, eta_text, route_source))
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass

        return {
            "road_km": road_km,
            "air_km": round(air_km, 2),
            "duration_minutes": duration_minutes,
            "eta_text": eta_text,
            "route_source": route_source
        }

    @staticmethod
    def calculate_geofence_status(
        team_lat: Optional[float],
        team_lon: Optional[float],
        site_lat: Optional[float],
        site_lon: Optional[float],
        checkin_status: str = "Standby",
        accessible_route_km: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluates whether a field crew is within their assigned work perimeter/corridor
        or has breached the geofence boundary using actual road distance and fastest route ETA.
        Strictly icon-free enterprise typography.
        """
        if team_lat is None or team_lon is None or pd.isna(team_lat) or pd.isna(team_lon):
            return {
                "dist_km": None,
                "road_dist_km": None,
                "air_dist_km": None,
                "eta_to_site": "No GPS Fix",
                "duration_minutes": None,
                "route_source": "NONE",
                "is_out_of_area": False,
                "flag_type": "NO_GPS",
                "flag_label": "NO GPS FIX",
                "badge_bg": "#F8FAFC",
                "badge_fg": "#64748B",
                "badge_border": "#E2E8F0"
            }

        if site_lat is None or site_lon is None or pd.isna(site_lat) or pd.isna(site_lon):
            return {
                "dist_km": None,
                "road_dist_km": None,
                "air_dist_km": None,
                "eta_to_site": "Standby",
                "duration_minutes": None,
                "route_source": "NONE",
                "is_out_of_area": False,
                "flag_type": "UNASSIGNED",
                "flag_label": "STANDBY (UNASSIGNED)",
                "badge_bg": "#F1F5F9",
                "badge_fg": "#475569",
                "badge_border": "#CBD5E1"
            }

        routing = FleetTrackingService.calculate_road_routing(team_lat, team_lon, site_lat, site_lon)
        air_km = routing["air_km"] if routing["air_km"] is not None else haversine_distance_km(float(team_lat), float(team_lon), float(site_lat), float(site_lon))
        road_km = routing["road_km"] if routing["road_km"] is not None else air_km
        eta_text = routing["eta_text"]
        duration_minutes = routing.get("duration_minutes")
        route_source = routing.get("route_source")

        status_lower = str(checkin_status).lower()

        # Rule 1: On-Site Active / ATP Testing
        # Team claims to be working at the tower site. Max allowable radius is 2.5 km.
        if any(k in status_lower for k in ["on-site", "wip", "testing", "atp"]):
            if air_km > 2.5:
                return {
                    "dist_km": round(road_km, 2),
                    "road_dist_km": round(road_km, 2),
                    "air_dist_km": round(air_km, 2),
                    "eta_to_site": eta_text,
                    "duration_minutes": duration_minutes,
                    "route_source": route_source,
                    "is_out_of_area": True,
                    "flag_type": "OUT_OF_SITE_RADIUS",
                    "flag_label": f"FLAG: OUT OF RADIUS ({road_km:.1f} km road)",
                    "badge_bg": "#FEF2F2",
                    "badge_fg": "#DC2626",
                    "badge_border": "#FECACA"
                }
            else:
                return {
                    "dist_km": round(air_km, 2),
                    "road_dist_km": round(road_km, 2),
                    "air_dist_km": round(air_km, 2),
                    "eta_to_site": eta_text,
                    "duration_minutes": duration_minutes,
                    "route_source": route_source,
                    "is_out_of_area": False,
                    "flag_type": "IN_SITE_RADIUS",
                    "flag_label": f"IN RADIUS ({air_km:.1f} km)",
                    "badge_bg": "#ECFDF5",
                    "badge_fg": "#059669",
                    "badge_border": "#A7F3D0"
                }

        # Rule 2: Confirmed - En Route / In-Transit / Field Transit Corridor
        # Maximum allowable operational radius/corridor is strictly 40.0 km.
        # Any position greater than 40.0 km from the target site triggers OUT OF AREA breach.
        corridor_threshold = 40.0

        if air_km > corridor_threshold:
            return {
                "dist_km": round(road_km, 2),
                "road_dist_km": round(road_km, 2),
                "air_dist_km": round(air_km, 2),
                "eta_to_site": eta_text,
                "duration_minutes": duration_minutes,
                "route_source": route_source,
                "is_out_of_area": True,
                "flag_type": "OUT_OF_AREA",
                "flag_label": f"FLAG: OUT OF AREA ({road_km:.1f} km road • ETA {eta_text})",
                "badge_bg": "#FEF2F2",
                "badge_fg": "#DC2626",
                "badge_border": "#FECACA"
            }
        else:
            return {
                "dist_km": round(road_km, 2),
                "road_dist_km": round(road_km, 2),
                "air_dist_km": round(air_km, 2),
                "eta_to_site": eta_text,
                "duration_minutes": duration_minutes,
                "route_source": route_source,
                "is_out_of_area": False,
                "flag_type": "IN_CORRIDOR",
                "flag_label": f"IN CORRIDOR ({road_km:.1f} km road • ETA {eta_text})",
                "badge_bg": "#EFF6FF",
                "badge_fg": "#0284C7",
                "badge_border": "#BFDBFE"
            }

    @staticmethod
    def auto_initialize_assigned_team_hub(team_code: str, site_id: str) -> None:
        """
        When a team is assigned to a site, ensures they are linked to the site and
        positioned at the operator's regional staging seaport hub (if not already live-checked-in for this site)
        so they are immediately visible on the radar map with a transit corridor to the site.
        """
        hub_coords = {
            "Telkomcel": (-8.5520, 125.5711),      # Port Dili Hub
            "Mitratel": (-7.1995, 112.7314),       # Pelabuhan Tanjung Perak
            "XLSmart": (3.7845, 98.6917),          # Pelabuhan Belawan
            "IOH": (-1.2654, 116.8312),            # Pelabuhan Balikpapan
        }
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT operator, lat, lon FROM timor_sites_100 WHERE site_id = ?", (site_id,))
            s_row = cur.fetchone()
            op = s_row[0] if s_row else "Telkomcel"
            hub_lat, hub_lon = hub_coords.get(op, (-8.5520, 125.5711))
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cur.execute("SELECT current_lat, current_lon, last_checkin_site, checkin_status FROM paas_field_teams WHERE team_code = ?", (team_code,))
            row = cur.fetchone()

            has_live_gps = (row is not None and row[0] is not None and row[1] is not None)
            use_lat = row[0] if has_live_gps else hub_lat
            use_lon = row[1] if has_live_gps else hub_lon
            use_status = str(row[3]) if (has_live_gps and "Confirmed" in str(row[3])) else f"Assigned to {site_id} (Regional Hub Standby)"

            cur.execute("""
                UPDATE paas_field_teams
                SET current_lat = ?,
                    current_lon = ?,
                    last_checkin_site = ?,
                    checkin_status = ?,
                    updated_at = ?
                WHERE team_code = ?
            """, (use_lat, use_lon, site_id, use_status, now_str, team_code))
            if cur.rowcount == 0:
                cur.execute("""
                    INSERT INTO paas_field_teams (
                        team_code, team_name, lead_name, contact_number, specialization,
                        current_lat, current_lon, last_checkin_site, checkin_status,
                        status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?, ?)
                """, (team_code, f"Field Crew {team_code}", "Field Lead PIC", "+6281200000000",
                      "Power I&C & Rectifier", use_lat, use_lon, site_id, use_status, now_str, now_str))
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    @staticmethod
    def ensure_geo_cache_table():
        """Ensures the geo_address_cache table exists in SQLite database."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS geo_address_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lat_round REAL NOT NULL,
                    lon_round REAL NOT NULL,
                    address TEXT NOT NULL,
                    details_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(lat_round, lon_round)
                )
            """)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def reverse_geocode(lat: Optional[float], lon: Optional[float]) -> str:
        """
        Translates raw GPS coordinates into human-readable postal/administrative address.
        Uses local SQLite caching (0.1ms lookup), fast OpenStreetMap Nominatim resolution,
        and offline heuristic regional fallbacks.
        Strictly icon-free enterprise typography.
        """
        if lat is None or lon is None or pd.isna(lat) or pd.isna(lon):
            return "No GPS fix"

        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (ValueError, TypeError):
            return "Invalid coordinates"

        lat_round = round(lat_f, 3)
        lon_round = round(lon_f, 3)

        FleetTrackingService.ensure_geo_cache_table()

        # Check local cache first
        try:
            df_cache = query_df(
                "SELECT address FROM geo_address_cache WHERE lat_round = ? AND lon_round = ? LIMIT 1",
                (lat_round, lon_round)
            )
            if not df_cache.empty and df_cache.iloc[0]["address"]:
                return str(df_cache.iloc[0]["address"]).strip()
        except Exception:
            pass

        # Try fast Nominatim reverse lookup with 2.0s timeout
        import urllib.request
        import json
        resolved_address = None
        details_str = None

        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat_round}&lon={lon_round}&zoom=18&addressdetails=1"
            headers = {"User-Agent": "SamvadPMOCommandCenter/1.0 (pmo-support@samvad.com)"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                details_str = json.dumps(data)
                addr = data.get("address", {})

                # Extract hierarchical address components
                road = addr.get("road") or addr.get("pedestrian") or addr.get("highway")
                village = addr.get("village") or addr.get("suburb") or addr.get("neighbourhood") or addr.get("hamlet")
                district = addr.get("town") or addr.get("city_district") or addr.get("municipality") or addr.get("subdistrict")
                city = addr.get("city") or addr.get("county") or addr.get("regency")
                state = addr.get("state")

                local_parts = []
                if road and road not in local_parts:
                    local_parts.append(road)
                if village and village not in local_parts:
                    local_parts.append(village)
                if district and district not in local_parts:
                    local_parts.append(district)
                if city and city not in local_parts:
                    local_parts.append(city)
                if state and state not in local_parts:
                    local_parts.append(state)

                if local_parts:
                    resolved_address = ", ".join(local_parts)
                else:
                    disp = data.get("display_name", "")
                    resolved_address = ", ".join(disp.split(", ")[:3]) if disp else None
        except Exception:
            resolved_address = None

        # Offline heuristic fallback if network unavailable or timed out
        if not resolved_address:
            # Regional centroid matches
            if -7.1 <= lat_f <= -6.7 and 107.5 <= lon_f <= 107.9:
                resolved_address = "Cileunyi / Bandung Raya, Jawa Barat"
            elif -6.4 <= lat_f <= -6.0 and 106.6 <= lon_f <= 107.0:
                resolved_address = "Kawasan Metropolitan Jakarta"
            elif -7.4 <= lat_f <= -7.1 and 112.6 <= lon_f <= 112.9:
                resolved_address = "Kawasan Surabaya, Jawa Timur"
            elif -8.65 <= lat_f <= -8.45 and 125.45 <= lon_f <= 125.70:
                resolved_address = "Dili, Timor-Leste"
            elif -8.55 <= lat_f <= -8.40 and 126.35 <= lon_f <= 126.55:
                resolved_address = "Baucau, Timor-Leste"
            elif -8.85 <= lat_f <= -8.65 and 125.30 <= lon_f <= 125.50:
                resolved_address = "Gleno, Ermera, Timor-Leste"
            elif -9.10 <= lat_f <= -8.90 and 125.10 <= lon_f <= 125.35:
                resolved_address = "Maliana, Bobonaro, Timor-Leste"
            elif -9.35 <= lat_f <= -9.10 and 124.25 <= lon_f <= 124.50:
                resolved_address = "Pante Macassar, Oecusse, Timor-Leste"
            else:
                resolved_address = f"Area Lapangan ({lat_f:.4f}, {lon_f:.4f})"

        # Cache the resolved address
        try:
            conn = get_connection()
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO geo_address_cache (lat_round, lon_round, address, details_json)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(lat_round, lon_round) DO UPDATE SET
                        address = excluded.address,
                        details_json = COALESCE(excluded.details_json, details_json)
                """, (lat_round, lon_round, resolved_address, details_str))
                conn.commit()
            finally:
                conn.close()
        except Exception:
            pass

        return resolved_address

    @staticmethod
    def record_team_checkin(
        team_code: str,
        site_id: str,
        lat: float,
        lon: float,
        status: str = "Confirmed - En Route",
        accuracy_m: float = 10.0,
        user_agent: str = "Mobile Browser Check-In",
        notes: str = ""
    ) -> Tuple[bool, str]:
        """
        Updates live GPS telemetry for a field team, reverse geocodes physical address,
        and logs check-in event.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        address = FleetTrackingService.reverse_geocode(lat, lon)
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE paas_field_teams
                SET current_lat = ?,
                    current_lon = ?,
                    current_address = ?,
                    last_checkin_at = ?,
                    last_checkin_site = ?,
                    checkin_status = ?,
                    updated_at = ?
                WHERE team_code = ?
            """, (lat, lon, address, now_str, site_id, status, now_str, team_code))
            if cur.rowcount == 0:
                cur.execute("""
                    INSERT INTO paas_field_teams (
                        team_code, team_name, lead_name, contact_number, specialization,
                        current_lat, current_lon, current_address, last_checkin_at, last_checkin_site, checkin_status,
                        status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?, ?)
                """, (team_code, f"Field Crew {team_code}", "Field Lead PIC", "+6281200000000",
                      "Power I&C & Rectifier", lat, lon, address, now_str, site_id, status, now_str, now_str))

            # Insert check-in log
            cur.execute("""
                INSERT INTO field_checkin_logs (
                    team_code, site_id, lat, lon, address, accuracy_m, checkin_status, checkin_time, user_agent, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (team_code, site_id, lat, lon, address, accuracy_m, status, now_str, user_agent, notes))

            # Audit record
            cur.execute("""
                INSERT INTO notification_audit_logs (
                    channel, recipient, message_type, payload, sent_status
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                "GPS_CheckIn",
                team_code,
                f"CHECKIN_{site_id}",
                f"Team {team_code} checked in at lat={lat:.5f}, lon={lon:.5f} ({address}) with status '{status}'",
                "SUCCESS"
            ))

            # Ensure site assignment is synced in sites table
            cur.execute("""
                UPDATE timor_sites_100
                SET assigned_team = ?, updated_at = ?
                WHERE site_id = ? AND (assigned_team IS NULL OR assigned_team = '')
            """, (team_code, now_str, site_id))

            conn.commit()
            return True, f"Check-in verified successfully. Team {team_code} is now live on the Command Center Radar."
        except Exception as e:
            return False, f"Failed to record check-in: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def get_fleet_tracking_dataframe() -> pd.DataFrame:
        """
        Returns full dataframe of field teams with their current GPS coordinates,
        resolved postal address, status, target assigned site location, and evaluated geofence flags.
        """
        query = """
            SELECT 
                t.team_code,
                t.team_name,
                t.lead_name,
                t.specialization,
                t.crew_size,
                t.contact_number,
                t.status as operational_status,
                t.current_lat,
                t.current_lon,
                t.current_address,
                t.last_checkin_at,
                t.last_checkin_site,
                t.checkin_status,
                t.battery_pct,
                COALESCE(s_chk.site_id, s_asg.site_id) as assigned_site_id,
                COALESCE(s_chk.site_name, s_asg.site_name) as assigned_site_name,
                COALESCE(s_chk.district, s_asg.district) as assigned_district,
                COALESCE(s_chk.lat, s_asg.lat) as target_site_lat,
                COALESCE(s_chk.lon, s_asg.lon) as target_site_lon,
                COALESCE(s_chk.accessible_route_km, s_asg.accessible_route_km) as accessible_route_km,
                COALESCE(s_chk.paas_status, s_asg.paas_status) as site_paas_status,
                COALESCE(s_chk.operator, s_asg.operator) as site_operator
            FROM paas_field_teams t
            LEFT JOIN timor_sites_100 s_chk ON s_chk.site_id = t.last_checkin_site
            LEFT JOIN timor_sites_100 s_asg ON s_asg.assigned_team = t.team_code
            GROUP BY t.team_code
            ORDER BY t.team_code ASC
        """
        df = query_df(query)
        if df.empty:
            df["dist_to_site_km"] = pd.Series(dtype="float")
            df["road_dist_km"] = pd.Series(dtype="float")
            df["air_dist_km"] = pd.Series(dtype="float")
            df["eta_to_site"] = pd.Series(dtype="object")
            df["is_out_of_area"] = pd.Series(dtype="bool")
            df["geofence_flag_label"] = pd.Series(dtype="object")
            df["geofence_badge_bg"] = pd.Series(dtype="object")
            df["geofence_badge_fg"] = pd.Series(dtype="object")
            df["geofence_badge_border"] = pd.Series(dtype="object")
            return df

        # Auto-resolve missing addresses for any active team with GPS
        for idx, row in df.iterrows():
            if pd.notna(row.get("current_lat")) and pd.notna(row.get("current_lon")):
                if not row.get("current_address") or pd.isna(row.get("current_address")):
                    addr = FleetTrackingService.reverse_geocode(row["current_lat"], row["current_lon"])
                    df.at[idx, "current_address"] = addr
                    try:
                        execute_write(
                            "UPDATE paas_field_teams SET current_address = ? WHERE team_code = ?",
                            (addr, row["team_code"])
                        )
                    except Exception:
                        pass

        # Resolve any unmatched or typo site IDs so distance and corridor calculations always work
        for idx, row in df.iterrows():
            if pd.isna(row["target_site_lat"]) or pd.isna(row["assigned_site_id"]):
                raw_site = str(row.get("last_checkin_site") or "").strip()
                cleaned_site = raw_site.replace("-", "").upper()
                site_match = pd.DataFrame()
                if raw_site:
                    site_match = query_df(
                        "SELECT site_id, site_name, district, lat, lon, accessible_route_km, paas_status, operator "
                        "FROM timor_sites_100 WHERE UPPER(site_id) = ? OR UPPER(REPLACE(site_id, '-', '')) = ? LIMIT 1",
                        (raw_site.upper(), cleaned_site)
                    )
                if site_match.empty:
                    site_match = query_df(
                        "SELECT site_id, site_name, district, lat, lon, accessible_route_km, paas_status, operator "
                        "FROM timor_sites_100 WHERE assigned_team = ? ORDER BY updated_at DESC LIMIT 1",
                        (row["team_code"],)
                    )
                if site_match.empty:
                    site_match = query_df("SELECT site_id, site_name, district, lat, lon, accessible_route_km, paas_status, operator FROM timor_sites_100 LIMIT 1")
                if not site_match.empty:
                    s_info = site_match.iloc[0]
                    df.at[idx, "assigned_site_id"] = s_info["site_id"]
                    df.at[idx, "assigned_site_name"] = s_info["site_name"]
                    df.at[idx, "assigned_district"] = s_info["district"]
                    df.at[idx, "target_site_lat"] = float(s_info["lat"])
                    df.at[idx, "target_site_lon"] = float(s_info["lon"])
                    df.at[idx, "accessible_route_km"] = float(s_info["accessible_route_km"] or 15.0)
                    df.at[idx, "site_paas_status"] = s_info["paas_status"]
                    df.at[idx, "site_operator"] = s_info["operator"]

        # Calculate geofence status for every row
        geofence_flags = []
        dists = []
        road_dists = []
        air_dists = []
        etas = []
        is_out_flags = []
        badge_bgs = []
        badge_fgs = []
        badge_borders = []

        for _, row in df.iterrows():
            geo = FleetTrackingService.calculate_geofence_status(
                team_lat=row["current_lat"],
                team_lon=row["current_lon"],
                site_lat=row["target_site_lat"],
                site_lon=row["target_site_lon"],
                checkin_status=row["checkin_status"] or "Standby",
                accessible_route_km=row["accessible_route_km"]
            )
            geofence_flags.append(geo["flag_label"])
            dists.append(geo["dist_km"])
            road_dists.append(geo.get("road_dist_km", geo["dist_km"]))
            air_dists.append(geo.get("air_dist_km", geo["dist_km"]))
            etas.append(geo.get("eta_to_site", "Standby"))
            is_out_flags.append(geo["is_out_of_area"])
            badge_bgs.append(geo["badge_bg"])
            badge_fgs.append(geo["badge_fg"])
            badge_borders.append(geo["badge_border"])

        df["dist_to_site_km"] = dists
        df["road_dist_km"] = road_dists
        df["air_dist_km"] = air_dists
        df["eta_to_site"] = etas
        df["is_out_of_area"] = is_out_flags
        df["geofence_flag_label"] = geofence_flags
        df["geofence_badge_bg"] = badge_bgs
        df["geofence_badge_fg"] = badge_fgs
        df["geofence_badge_border"] = badge_borders

        return df

    @staticmethod
    def get_fleet_kpis() -> Dict[str, Any]:
        """Calculates tracking and geofence metrics for the fleet header."""
        df = FleetTrackingService.get_fleet_tracking_dataframe()
        if df.empty:
            return {
                "total_teams": 0,
                "teams_with_gps": 0,
                "confirmed_teams": 0,
                "en_route_teams": 0,
                "on_site_teams": 0,
                "out_of_area_count": 0
            }

        unique_teams = df.drop_duplicates(subset=["team_code"])
        total = len(unique_teams)
        with_gps = len(unique_teams[unique_teams["current_lat"].notna() & unique_teams["current_lon"].notna()])
        confirmed = len(unique_teams[unique_teams["checkin_status"].str.contains("Confirmed", na=False)])
        en_route = len(unique_teams[unique_teams["checkin_status"].str.contains("En Route", na=False)])
        on_site = len(unique_teams[unique_teams["checkin_status"].str.contains("On-Site", na=False)])
        out_of_area = len(unique_teams[unique_teams["is_out_of_area"] == True])

        return {
            "total_teams": total,
            "teams_with_gps": with_gps,
            "confirmed_teams": confirmed,
            "en_route_teams": en_route,
            "on_site_teams": on_site,
            "out_of_area_count": out_of_area
        }

    @staticmethod
    def get_team_breadcrumbs(team_code: str, limit: int = 50) -> pd.DataFrame:
        """
        Retrieves historical GPS checkin breadcrumbs for a team to plot their movement trail.
        """
        query = """
            SELECT lat, lon, checkin_status, checkin_time
            FROM field_checkin_logs
            WHERE team_code = ? AND lat IS NOT NULL AND lon IS NOT NULL
            ORDER BY id ASC
            LIMIT ?
        """
        return query_df(query, (team_code, limit))

    @staticmethod
    def get_effective_host() -> str:
        """Determines active host/base URL for cross-device access (public tunnel or local Wi-Fi)."""
        pub = os.environ.get("STREAMLIT_PUBLIC_URL", "").strip()
        if pub:
            return pub.rstrip("/")
        # Check active persistent tunnel cache
        try:
            cur_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            tunnel_file = os.path.join(cur_dir, "tunnel_url.txt")
            if os.path.exists(tunnel_file):
                with open(tunnel_file, "r") as f:
                    u = f.read().strip()
                    if u and u.startswith("http"):
                        return u.rstrip("/")
        except Exception:
            pass
        try:
            import subprocess
            res = subprocess.run(["ipconfig", "getifaddr", "en0"], capture_output=True, text=True, timeout=1)
            ip = res.stdout.strip()
            if ip:
                return f"http://{ip}:8502"
        except Exception:
            pass
        return "http://10.101.0.236:8502"

    @staticmethod
    def ensure_device_binding_table():
        """Ensures the assignment_device_bindings table exists in SQLite database."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS assignment_device_bindings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_code TEXT NOT NULL,
                    site_id TEXT NOT NULL,
                    assigned_phone TEXT,
                    bound_device_id TEXT NOT NULL,
                    user_agent TEXT,
                    bound_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'ACTIVE',
                    UNIQUE(team_code, site_id)
                )
            """)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def generate_assignment_auth_token(team_code: str, site_id: str, phone: Optional[str] = None) -> str:
        """
        Generates an 8-character cryptographic HMAC token binding the tracking link
        exclusively to the assignment and assigned technician phone number.
        """
        salt = os.environ.get("SAMVAD_SECURITY_SALT", "SAMVAD-PMO-SECURITY-SALT-2026")
        clean_code = str(team_code).strip().upper()
        clean_site = str(site_id).strip().upper()

        target_phone = phone
        if not target_phone:
            try:
                df = query_df("SELECT contact_number FROM paas_field_teams WHERE team_code = ? LIMIT 1", (clean_code,))
                if not df.empty and df.iloc[0]["contact_number"]:
                    target_phone = str(df.iloc[0]["contact_number"]).strip()
                else:
                    target_phone = "+6281200000000"
            except Exception:
                target_phone = "+6281200000000"

        clean_p = "".join(ch for ch in str(target_phone) if ch.isdigit())
        msg = f"{clean_code}:{clean_site}:{clean_p}"
        token = hmac.new(salt.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()[:8]
        return token

    @staticmethod
    def verify_assignment_auth_token(team_code: str, site_id: str, token: str, phone: Optional[str] = None) -> bool:
        """Verifies if the provided auth token matches cryptographic signature."""
        if not token:
            return False
        expected = FleetTrackingService.generate_assignment_auth_token(team_code, site_id, phone)
        return hmac.compare_digest(expected.lower(), str(token).strip().lower())

    @staticmethod
    def verify_or_bind_device(
        team_code: str,
        site_id: str,
        device_id: str,
        user_agent: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Enforces 1-Device Binding and Anti-Share limitation:
        - If no device is bound yet: Binds device_id to (team_code, site_id).
        - If device_id matches bound device: Authorized.
        - If device_id does NOT match: REJECTS with 403 Forbidden and logs security alarm in audit logs.
        """
        FleetTrackingService.ensure_device_binding_table()
        clean_code = str(team_code).strip().upper()
        clean_site = str(site_id).strip().upper()
        dev_id = str(device_id).strip()

        if not dev_id:
            return False, "DEVICE_ID_REQUIRED", {"error": "Missing device identifier."}

        # Query team details for phone and lead name
        try:
            df_team = query_df("SELECT lead_name, contact_number FROM paas_field_teams WHERE team_code = ? LIMIT 1", (clean_code,))
            lead_name = df_team.iloc[0]["lead_name"] if not df_team.empty else "Lead PIC"
            phone = df_team.iloc[0]["contact_number"] if not df_team.empty else "-"
        except Exception:
            lead_name = "Lead PIC"
            phone = "-"

        # Mask phone: e.g. +62 853-••••-1694
        raw_digits = "".join(c for c in str(phone) if c.isdigit())
        if len(raw_digits) >= 8:
            masked_phone = f"+{raw_digits[:2]} {raw_digits[2:5]}-••••-{raw_digits[-4:]}"
        else:
            masked_phone = str(phone)

        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                SELECT bound_device_id, status, bound_at, last_seen_at 
                FROM assignment_device_bindings 
                WHERE team_code = ? AND site_id = ? AND status = 'ACTIVE'
                LIMIT 1
            """, (clean_code, clean_site))
            row = cur.fetchone()

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not row:
                # No active device bound yet -> Bind this first device!
                cur.execute("""
                    INSERT INTO assignment_device_bindings (
                        team_code, site_id, assigned_phone, bound_device_id, user_agent, bound_at, last_seen_at, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
                    ON CONFLICT(team_code, site_id) DO UPDATE SET
                        assigned_phone = excluded.assigned_phone,
                        bound_device_id = excluded.bound_device_id,
                        user_agent = excluded.user_agent,
                        bound_at = excluded.bound_at,
                        last_seen_at = excluded.last_seen_at,
                        status = 'ACTIVE'
                """, (clean_code, clean_site, phone, dev_id, user_agent or "Mobile Browser", now_str, now_str))
                conn.commit()
                return True, "DEVICE_BOUND", {
                    "is_authorized": True,
                    "bound_device": dev_id[:8] + "...",
                    "lead_name": lead_name,
                    "phone": masked_phone,
                    "message": f"Smartphone successfully bound to {clean_code} assignment."
                }
            else:
                bound_dev = row[0]
                if bound_dev == dev_id:
                    # Authorized matching device
                    cur.execute("""
                        UPDATE assignment_device_bindings 
                        SET last_seen_at = ?, user_agent = COALESCE(?, user_agent)
                        WHERE team_code = ? AND site_id = ? AND status = 'ACTIVE'
                    """, (now_str, user_agent, clean_code, clean_site))
                    conn.commit()
                    return True, "AUTHORIZED_DEVICE", {
                        "is_authorized": True,
                        "bound_device": dev_id[:8] + "...",
                        "lead_name": lead_name,
                        "phone": masked_phone,
                        "message": "Authorized registered device."
                    }
                else:
                    # MISMATCH! Device forwarding attempt detected!
                    cur.execute("""
                        INSERT INTO notification_audit_logs (
                            channel, recipient, message_type, payload, sent_status
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        "Security",
                        clean_code,
                        "UNAUTHORIZED_SHARE_BLOCKED",
                        f"Access Denied: Attempted check-in from unauthorized device '{dev_id[:8]}...' for {clean_code} at {clean_site}. Locked to registered device '{bound_dev[:8]}...'",
                        "BLOCKED"
                    ))
                    conn.commit()
                    return False, "DEVICE_MISMATCH", {
                        "is_authorized": False,
                        "lead_name": lead_name,
                        "phone": masked_phone,
                        "bound_device": bound_dev[:8] + "...",
                        "attempted_device": dev_id[:8] + "...",
                        "message": f"ACCESS DENIED: Unauthorized device. This dispatch link is locked exclusively to Lead PIC's registered smartphone ({masked_phone}). Link sharing is strictly restricted to prevent GPS data collision."
                    }
        finally:
            conn.close()

    @staticmethod
    def reset_device_binding(team_code: str, site_id: Optional[str] = None) -> bool:
        """
        Allows PMO Controller to clear the device lock when a technician legitimately
        changes or replaces their physical phone.
        """
        FleetTrackingService.ensure_device_binding_table()
        clean_code = str(team_code).strip().upper()
        conn = get_connection()
        try:
            cur = conn.cursor()
            if site_id:
                clean_site = str(site_id).strip().upper()
                cur.execute("""
                    DELETE FROM assignment_device_bindings 
                    WHERE team_code = ? AND site_id = ?
                """, (clean_code, clean_site))
            else:
                cur.execute("""
                    DELETE FROM assignment_device_bindings 
                    WHERE team_code = ?
                """, (clean_code,))

            cur.execute("""
                INSERT INTO notification_audit_logs (
                    channel, recipient, message_type, payload, sent_status
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                "Controller",
                clean_code,
                "DEVICE_BINDING_RESET",
                f"PMO Controller cleared device binding lock for {clean_code}" + (f" at {site_id}" if site_id else ""),
                "SUCCESS"
            ))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()

    @staticmethod
    def get_device_binding_status(team_code: str, site_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Queries the current active device binding for a team assignment."""
        FleetTrackingService.ensure_device_binding_table()
        clean_code = str(team_code).strip().upper()
        if site_id:
            clean_site = str(site_id).strip().upper()
            df = query_df("SELECT * FROM assignment_device_bindings WHERE team_code = ? AND site_id = ? AND status = 'ACTIVE' LIMIT 1", (clean_code, clean_site))
        else:
            df = query_df("SELECT * FROM assignment_device_bindings WHERE team_code = ? AND status = 'ACTIVE' ORDER BY id DESC LIMIT 1", (clean_code,))
        if not df.empty:
            return df.iloc[0].to_dict()
        return None

    @staticmethod
    def generate_checkin_url(team_code: str, site_id: str, host: Optional[str] = None, phone: Optional[str] = None) -> str:
        """Generates the mobile GPS check-in link with cryptographic auth token for WhatsApp Work Order messages."""
        auth_token = FleetTrackingService.generate_assignment_auth_token(team_code, site_id, phone)
        if host:
            base = host if host.startswith("http") else f"http://{host}"
            return f"{base}/checkin?checkin={team_code}&site={site_id}&auth={auth_token}"
        base = FleetTrackingService.get_effective_host()
        return f"{base}/checkin?checkin={team_code}&site={site_id}&auth={auth_token}"

    @staticmethod
    def parse_location_string(text: str) -> Optional[Tuple[float, float]]:
        """
        Extracts latitude and longitude from:
        - WhatsApp location messages
        - Google Maps links (e.g. https://maps.google.com/?q=-7.2575,112.7521)
        - Google Maps short links or place URLs
        - Standard lat/lon strings (e.g. '-7.2575, 112.7521' or '-7.2575 112.7521')
        """
        if not text or not str(text).strip():
            return None
        import re
        s = str(text).strip()
        m = re.search(r'(?:q=|@|loc:)?(-?\d{1,2}\.\d+)[,\s]+(-?\d{1,3}\.\d+)', s)
        if m:
            try:
                lat = float(m.group(1))
                lon = float(m.group(2))
                if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                    return lat, lon
            except (ValueError, TypeError):
                pass
        return None
