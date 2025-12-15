"""
Keyword-based categorizer for news articles.
Uses Dutch keywords to assign categories.
"""
from .models import Category


def assign_category(title='', summary='', content=''):
    """
    Assign category based on keyword matching.
    
    Args:
        title: Article title
        summary: Article summary
        content: Article content
    
    Returns:
        Category instance or None
    """
    # Combine all text for matching
    text = f"{title} {summary} {content}".lower()
    
    # Keyword mappings (order matters - first match wins)
    # Order: Trump, Russia (most specific), then Politics, National, International, Sport
    # Note: Trump and Russia are checked first as they are very specific categories
    keyword_rules = [
        # Trump - check for Trump mentions (case-insensitive, checked first)
        {
            'keywords': [
                'trump',
            ],
            'category_key': Category.TRUMP
        },
        # Russia - check for "Rusland" in fulltext (case-insensitive, checked early)
        {
            'keywords': [
                'rusland',
            ],
            'category_key': Category.RUSSIA
        },
        # Politics - more specific political terms, avoiding generic words
        {
            'keywords': [
                # Political institutions and processes
                'kabinet', 'tweede kamer', 'eerste kamer', 'politiek', 'minister',
                'premier', 'coalitie', 'verkiezingen', 'partij', 'staatssecretaris',
                'regering', 'motie', 'wetsvoorstel', 'kabinetsformatie', 'kabinetscrisis',
                # Political parties (specific)
                'rutte', 'wilders', 'pvv', 'vvd', 'd66', 'cda', 'groenlinks', 'pvda', 
                'sp', 'fvd', 'christenunie', 'sgp', 'denk', 'volt', 'ja21',
                # Political processes (avoid generic "overheid" which appears in legal contexts)
                'kabinetsdebat', 'kamerdebat', 'motie van wantrouwen', 'kabinet valt',
                'formatie', 'verkiezingsprogramma', 'regeerakkoord'
            ],
            'category_key': Category.POLITICS
        },
        # National - legal/court terms FIRST to catch legal news before Politics
        {
            'keywords': [
                # Legal/court terms (highest priority - checked first in National)
                # These MUST come before Politics to catch legal news
                'vrijgesproken', 'opruiing', 'rechtbank', 'rechter', 'openbaar ministerie',
                'aangeklaagd', 'veroordeeld', 'vonnis', 'zaak', 'verdachte', 'dader',
                'slachtoffer', 'beschuldigd', 'verdediging', 'aanklager', 'gerecht',
                'hof', 'cassatie', 'appel', 'kantonrechter', 'krijgsraad',
                'aanklacht', 'beschuldiging', 'strafrecht', 'strafbaar',
                'sepot', 'geseponeerd', 'inbeschuldigingstelling', 'aangifte',
                'getuige', 'verhoor', 'verhoren', 'verhoorcommissie', 'officier',
                'juridisch', 'jurisprudentie', 'arrest', 'uitspraak', 'uitspraken',
                'presentator', 'presentatoren',  # Media personalities often national news
                # Police/security
                'politie', 'aivd', 'marechaussee', 'justitie', 'gevangenis', 'detentie',
                # National institutions
                'nederland', 'nederlands', 'provincie', 'gemeente', 'randstad',
                'rijkswaterstaat', 'rijksoverheid', 'rijksdienst',
                # Infrastructure
                'trein', 'ns', 'schiphol', 'luchthaven', 'metro', 'tram', 'bus',
                'wegen', 'snelweg', 'a2', 'a4', 'a12', 'a27', 'a50', 'a73',
                # Public services
                'zorg', 'onderwijs', 'belastingdienst', 'belasting', 'cbs',
                'knmi', 'weer', 'weersverwachting', 'meteorologie',
                # National events/people
                'koningshuis', 'koning', 'koningin', 'prins', 'prinses', 'beatrix',
                'willem-alexander', 'maxima', 'amalia',
                # Social/cultural (national scope)
                'woon', 'woning', 'huur', 'koop', 'crisis', 'inflatie', 'economie',
                'werkloosheid', 'werkgelegenheid', 'zzp', 'pensioen', 'aow',
                # National news markers
                'binnenland', 'binnenlands', 'nationaal', 'landelijk'
            ],
            'category_key': Category.NATIONAL
        },
        # International
        {
            'keywords': [
                'europa', 'eu', 'europese unie', 'eurozone', 'brussel', 'strasbourg',
                'vs', 'verenigde staten', 'amerika', 'washington', 'biden',
                'putin', 'moskou', 'oekraïne', 'kiev', 'zelensky',
                'china', 'peking', 'beijing', 'xi jinping', 'midden-oosten',
                'israël', 'palestina', 'gaza', 'jeruzalem', 'iran', 'syrië',
                'verenigde naties', 'vn', 'un', 'navo', 'nato', 'buitenland',
                'internationaal', 'conflict', 'oorlog', 'vredesoverleg', 'grens',
                'diplomatie', 'ambassade', 'consulaat', 'migrant', 'vluchteling',
                'asiel', 'immigratie', 'grenscontrole'
            ],
            'category_key': Category.INTERNATIONAL
        },
        # Sport - more specific to avoid false matches
        {
            'keywords': [
                # Football/soccer
                'ajax', 'psv', 'feyenoord', 'oranje', 'voetbal', 'eredivisie',
                'europa league', 'champions league', 'beker', 'nederlands elftal',
                'wk', 'wereldkampioenschap voetbal', 'ek', 'europese kampioenschap',
                # Motorsports
                'formule 1', 'f1', 'max verstappen', 'verstappen', 'zandvoort',
                'grand prix', 'circuit', 'race', 'coureur',
                # Cycling
                'wielrennen', 'tour de france', 'giro', 'vuelta', 'ronde van',
                # Tennis
                'tennis', 'wimbledon', 'roland garros', 'us open', 'australian open',
                # Olympics
                'olympisch', 'olympiade', 'olympische spelen', 'tokio', 'paris',
                # Other sports
                'schaatsen', 'shorttrack', 'hockey', 'basketbal', 'volleybal',
                # Sports terms (must be in sports context)
                # Note: Avoiding generic words like 'overwinning' and 'nederlaag' 
                # that could match in non-sport contexts
                'sport', 'sportief', 'sportieve', 'wedstrijd', 'competitie', 
                'kampioen', 'kampioenschap', 'atleet', 'sportman', 'sportvrouw', 
                'trainer', 'coach', 'scheidsrechter', 'doelpunt', 'goal', 
                'score', 'sportstand', 'punt', 'sportoverwinning', 'sportnederlaag',
                'sportresultaat', 'sportuitslag', 'sportnieuws'
            ],
            'category_key': Category.SPORT
        },
    ]
    
    # Check each rule in order
    for rule in keyword_rules:
        for keyword in rule['keywords']:
            if keyword in text:
                try:
                    category = Category.objects.get(key=rule['category_key'])
                    return category
                except Category.DoesNotExist:
                    # Category not created yet, continue
                    pass
    
    # Default to OTHER if no match
    try:
        return Category.objects.get(key=Category.OTHER)
    except Category.DoesNotExist:
        return None

