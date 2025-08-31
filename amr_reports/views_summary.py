from django.http import JsonResponse
from django.db import connection

def _q1(sql):
    with connection.cursor() as cur:
        cur.execute(sql)
        return cur.fetchone()[0]

def counts_summary(request):
    """
    Returns { total_results, unique_patients, organisms_count }
    """
    try:
        total = _q1("SELECT COUNT(*) FROM amr_reports_labresult")
        uniq  = _q1("SELECT COUNT(DISTINCT patient_id) FROM amr_reports_labresult")
        orgs  = _q1("SELECT COUNT(DISTINCT organism) FROM amr_reports_labresult")
        return JsonResponse({
            "total_results": total,
            "unique_patients": uniq,
            "organisms_count": orgs
        })
    except Exception as e:
        return JsonResponse({"detail": f"counts_summary error: {e}"}, status=500)

# ----- safe placeholders so other tabs don't 500 -----

def resistance_time_trend(request):
    # TODO: replace with real data; keeping shape stable for the UI
    return JsonResponse({"series": []})

def antibiogram(request):
    # TODO: replace with real data
    return JsonResponse({"rows": []})

def data_quality(request):
    # TODO: replace with real checks
    return JsonResponse({"issues": []})

def facilities_geo(request):
    # Minimal GeoJSON so maps tab doesn't crash
    return JsonResponse({"type":"FeatureCollection","features":[]})



def lab_results(request):
    """Return recent lab results with safe fallbacks (never 500)."""
    try:
        with connection.cursor() as cur:
            # Table exists?
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='amr_reports_labresult'")
            if not cur.fetchone():
                return JsonResponse({"results": []})

            # Columns that actually exist
            cur.execute("PRAGMA table_info(amr_reports_labresult)")
            cols_in_db = {row[1] for row in cur.fetchall()}  # column names in this DB

            # Try our preferred order, but only keep ones present in the DB
            preferred = [
                "id","facility","patient_id","sex","age",
                "specimen_type","organism","antibiotic",
                "ast_result","test_date","host_type"
            ]
            cols = [c for c in preferred if c in cols_in_db]

            # Absolute fallback: if none of the preferred columns exist, select whatever exists
            if not cols_in_db:
                return JsonResponse({"results": []})
            if not cols:
                cols = sorted(cols_in_db)  # select all available columns

            sql = "SELECT " + ", ".join(cols) + " FROM amr_reports_labresult ORDER BY id DESC LIMIT 50"
            cur.execute(sql)
            rows = cur.fetchall()
            out = [dict(zip(cols, r)) for r in rows]
            return JsonResponse({"results": out})
    except Exception as e:
        return JsonResponse({"detail": f"lab_results error: {type(e).__name__}: {e}"}, status=500)

