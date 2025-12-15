"""
Context processors for web app.
"""
from apps.feed_ingest.models import IngestionRun


def error_banner(request):
    """
    Context processor to add error banner info.
    Shows error banner if latest ingestion run failed without subsequent success.
    """
    latest_failed = IngestionRun.get_latest_failed()
    
    if latest_failed:
        return {
            'ingestion_error': {
                'show': True,
                'timestamp': latest_failed.started_at,
                'message': latest_failed.error_message or 'Onbekende fout',
            }
        }
    
    return {
        'ingestion_error': None
    }

