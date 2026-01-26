# Admin Pagina - Email Adressen Setup

Om echte email adressen te tonen in de admin pagina, moet je een database functie aanmaken in Supabase.

## 📋 Stap 1: Voer SQL Functie Uit

1. Ga naar je **Supabase Dashboard**
2. Open de **SQL Editor**
3. Kopieer en plak de inhoud van `admin_get_user_emails.sql`
4. Klik op **Run** om de functies aan te maken

**⚠️ BELANGRIJK:** De functie `get_all_users_with_reading_stats()` is aangepast om **ALLE geregistreerde gebruikers** uit `auth.users` op te halen, niet alleen diegenen met activiteit. Als je de functie al had aangemaakt, voer het script opnieuw uit om de update te krijgen.

## 🔧 Wat wordt er aangemaakt?

### Functie 1: `get_user_emails(user_ids UUID[])`
Haalt email adressen op voor een lijst van user IDs.

### Functie 2: `get_all_users_with_reading_stats()`
Haalt **ALLE geregistreerde gebruikers** uit `auth.users` op met hun reading statistics en email adressen in één query. Gebruikers zonder activiteit worden ook getoond (met 0 statistieken).

## ✅ Verificatie

Na het uitvoeren van de SQL:

1. Ga naar de admin pagina: `[jouw-url]?page=Admin`
2. Je zou nu echte email adressen moeten zien in plaats van "user_xxxxx"

## 🔒 Beveiliging

De functies gebruiken `SECURITY DEFINER`, wat betekent dat ze worden uitgevoerd met de rechten van de functie eigenaar (meestal de database superuser). Dit is nodig om toegang te krijgen tot de `auth.users` tabel.

**Permissions:**
- `GRANT EXECUTE ON FUNCTION get_user_emails(UUID[]) TO authenticated;`
- `GRANT EXECUTE ON FUNCTION get_all_users_with_reading_stats() TO authenticated;`

Dit betekent dat alleen ingelogde gebruikers deze functies kunnen aanroepen.

## 🐛 Troubleshooting

### Functie bestaat niet error
Als je een error krijgt dat de functie niet bestaat:
- Controleer of je de SQL correct hebt uitgevoerd
- Controleer of je in de juiste database bent
- Kijk in de Supabase logs voor meer details

### Geen emails zichtbaar
Als je nog steeds geen emails ziet:
- Controleer of de functie correct is aangemaakt
- Kijk in de browser console voor errors
- Controleer of gebruikers daadwerkelijk zijn geregistreerd met email adressen

### Permission denied
Als je een permission error krijgt:
- Controleer of de GRANT statements zijn uitgevoerd
- Zorg dat je ingelogd bent als gebruiker
- Controleer de RLS policies

## 💡 Alternatief (Zonder Database Functie)

Als je de database functie niet kunt gebruiken, zal de code automatisch terugvallen op een fallback methode die probeert emails op te halen via de `get_user_emails` functie. Als die ook niet beschikbaar is, worden placeholder emails getoond.
