# Admin Pagina

De admin pagina toont een overzicht van alle geregistreerde gebruikers en hun leesstatistieken.

## 🔗 Toegang

De admin pagina is bereikbaar via:

```
[jouw-website-url]?page=Admin
```

**Voorbeeld:**
- Lokaal: `http://localhost:8501?page=Admin`
- Productie: `https://jouw-app.streamlit.app?page=Admin`

## 📊 Functionaliteit

De admin pagina toont:

1. **Overzicht Metrics:**
   - Totaal aantal gebruikers
   - Totaal aantal gelezen artikelen
   - Totaal aantal geopende artikelen
   - Gemiddeld aantal gelezen artikelen per gebruiker

2. **Gebruikers Tabel:**
   - Gebruiker ID (verkort)
   - Email (indien beschikbaar)
   - Aantal artikelen geopend
   - Aantal artikelen gelezen
   - Gemiddelde leesduur (in seconden)
   - Leespercentage

3. **Export Functionaliteit:**
   - Download de data als CSV bestand

## 🔒 Beveiliging

**Let op:** De admin pagina is momenteel niet beveiligd met speciale admin rechten. Iedereen die ingelogd is kan de pagina bekijken.

Voor productie gebruik, overweeg:

1. **Admin Check Toevoegen:**
   - Controleer of de gebruiker admin rechten heeft
   - Gebruik een admin_users tabel of check op specifieke email

2. **Service Role Key:**
   - Gebruik Supabase Service Role Key voor admin functies
   - Dit geeft volledige toegang tot de database

3. **Row Level Security:**
   - Zorg dat RLS policies correct zijn ingesteld
   - Admin functies kunnen een aparte tabel gebruiken

## 💡 Toekomstige Verbeteringen

- [ ] Email adressen ophalen van gebruikers (vereist service role key of database functie)
- [ ] Admin authenticatie toevoegen
- [ ] Filters en zoekfunctie in de tabel
- [ ] Sortering op verschillende kolommen
- [ ] Paginering voor grote aantallen gebruikers
- [ ] Grafieken en visualisaties
- [ ] Export naar Excel/PDF

## 🛠️ Technische Details

De admin pagina gebruikt:
- `get_all_users_with_reading_stats_via_activity()` - Haalt gebruikers op uit reading_activity tabel
- `get_reading_statistics()` - Berekent statistieken per gebruiker
- Pandas DataFrame voor tabel weergave
- Streamlit data editor voor interactieve tabel
