from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import hashlib
import math

def hash_image(filepath):
    """Return SHA-256 hash of the file contents."""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def _to_degrees(value):
    """Convert EXIF GPS tuple (deg, min, sec) to decimal degrees."""
    d, m, s = value
    return float(d) + float(m) / 60 + float(s) / 3600

def read_exif(filepath):
    """Read EXIF from image. Returns dict with date_taken, gps_lat, gps_lng, device.
       Missing fields are None. Never raises on failure."""
    result = {'date_taken': None, 'gps_lat': None, 'gps_lng': None, 'device': None}
    try:
        img = Image.open(filepath)
        exif = img.getexif()
        if not exif:
            return result

        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            if tag == 'DateTime':
                result['date_taken'] = str(value)
            elif tag == 'Make':
                result['device'] = str(value)

        gps_ifd = exif.get_ifd(0x8825)
        if gps_ifd:
            gps_data = {GPSTAGS.get(k, k): v for k, v in gps_ifd.items()}
            if 'GPSLatitude' in gps_data and 'GPSLatitudeRef' in gps_data:
                lat = _to_degrees(gps_data['GPSLatitude'])
                if gps_data['GPSLatitudeRef'] == 'S':
                    lat = -lat
                result['gps_lat'] = round(lat, 6)
            if 'GPSLongitude' in gps_data and 'GPSLongitudeRef' in gps_data:
                lng = _to_degrees(gps_data['GPSLongitude'])
                if gps_data['GPSLongitudeRef'] == 'W':
                    lng = -lng
                result['gps_lng'] = round(lng, 6)
    except Exception:
        pass
    return result

def haversine_km(lat1, lng1, lat2, lng2):
    """Distance between two coordinates in km (great-circle)."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))

def is_within_boundary(photo_lat, photo_lng, project_lat, project_lng, radius_km=2.0):
    """True if photo location is within radius_km of the project center."""
    if None in (photo_lat, photo_lng, project_lat, project_lng):
        return False
    return haversine_km(photo_lat, photo_lng, project_lat, project_lng) <= radius_km

def check_duplicate(photo_hash, conn, exclude_report_id=None):
    """Look for another report with the same photo_hash.
       Returns (is_duplicate, other_report_id)."""
    if not photo_hash:
        return False, None
    query = 'SELECT report_id FROM citizen_reports WHERE photo_hash = ?'
    params = [photo_hash]
    if exclude_report_id is not None:
        query += ' AND report_id != ?'
        params.append(exclude_report_id)
    row = conn.execute(query, params).fetchone()
    if row:
        return True, row['report_id']
    return False, None
