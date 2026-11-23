# Routes uitvoeren

Gebruik Python 3.10+ en het absolute pad van deze skill. De scripts schrijven
naar een eigen tijdelijke map buiten de repository, tonen het rapportpad en
laten bestaande bronnen en instellingen ongemoeid. Geen extra Python-packages.
De scripts bewaren `report.md` en `evidence.json`; lees deze als bronmateriaal.

## Lokaal

Vereist: actuele `yt-dlp`, `ffmpeg`, `ffprobe` en een voor YouTube ondersteunde
JavaScript-runtime. Controleer bij een downloadfout eerst versie en foutmelding.
Werk tools alleen bij binnen de gegeven toestemming; omzeil geen TLS-controles
en ga niet automatisch browsercookies ophalen. De helper negeert bestaande
yt-dlp-configs en kiest een aanwezige Deno-, Node- of Bun-runtime expliciet.
Gebruikershooks, cookiekeuzes en proxyinstellingen worden niet overgenomen.
Er is geen Whisper-installatie of automatische audioupload.

```bash
python3 "<skill-dir>/scripts/local.py" "https://www.youtube.com/watch?v=..."
python3 "<skill-dir>/scripts/local.py" "<eerder-gedownloade-video>" --timestamps 05:44,06:46
python3 "<skill-dir>/scripts/local.py" "<url>" --transcript-only
```

Begin voor gesproken uitleg met `--transcript-only`. Zijn daarna beelden nodig,
gebruik de URL met `--skip-captions` zodat ondertitels niet opnieuw worden
opgevraagd. Voor vragen over demonstraties mag de beeldroute meteen lopen.
Bij lange talks of livestreams: begin met transcript, kies een beperkt aantal
beelden en zet `--out-dir` op schijf als de tijdelijke map RAM gebruikt.
`--timestamps` beperkt de beeldselectie, maar de URL-route downloadt nog steeds
de volledige video. Er is geen segmentdownload.

Standaard maximaal 24 intervalbeelden op 1280px breed over de hele tijdlijn.
`--timestamps` kiest in plaats daarvan specifieke momenten; `--max-frames`
(1 t/m 100) en `--width` (320 t/m 1920) begrenzen selectie en leesbaarheid.
Er is geen scèneherkenning: korte schermwissels kunnen ontbreken. Selecteer
extra tijdcodes wanneer een demonstratie dat vereist. De JSON bevat de
gevraagde tijdcodes en beeldpaden. FFmpeg zoekt naar het bronmoment; de selectie
is geen garantie op frame-exacte timing.

Het script kiest maximaal één ondertiteltrack: handmatig in de oorspronkelijke
taal wanneer herkenbaar, anders originele automatische ondertitels, daarna
Engels of de eerste beschikbare taal. Het rapport noemt soort en taal, ook
wanneer die keuze mogelijk een vertaling is. Lees bij voorkeur het compacte
`transcript.txt` met tijdcodes: de helper verwijdert
VTT-tags en, alleen bij automatische captions, overlappende rolling tekst.
Handmatige ondertitels behouden herhaalde woorden tussen cues. De originele
VTT blijft behouden voor exacte citaten en twijfel over herhaling; normalisatie
kan geen onderscheid garanderen tussen captionherhaling en gesproken herhaling.

De videodownload krijgt maximaal 3600 seconden (`--download-timeout` is
instelbaar); metadata, captions en framecalls maximaal 300 seconden per stap.
Netwerkstilstand blijft begrensd door `--socket-timeout 20`. Fouten bewaren een
korte foutregel met URLs en herkenbare credentialvelden verwijderd.

Metadata, captions en video worden afzonderlijk opgehaald. Een captionfout
blokkeert de beeldroute niet. Een fout of ontbrekende modaliteit staat in het
rapport; exit 2 betekent gedeeltelijk inhoudelijk bewijs, exit 1 geen captions
of beelden. Alleen metadata is broncontext, geen bewijs van de video-inhoud.
Ontbrekend transcript wordt niet vanzelf door spraakherkenning aangevuld.
Bij een lokaal videobestand worden alleen beelden verzameld.

HTTP 429: stop met captionrequests en respecteer de beperking. HTTP 403: controleer
de actuele yt-dlp en JS-runtime; hoogstens één gerichte herpoging na een bewezen
correctie. De scripts proberen niet automatisch opnieuw. Hergebruik de lokale
video voor extra beelden. Gebruik `--out-dir <parent>` alleen voor een gekozen
bewijslocatie; elke run maakt daar een nieuwe eigen submap.

## Gemini via OpenRouter

```bash
python3 "<skill-dir>/scripts/openrouter.py" "https://www.youtube.com/watch?v=..." \
  --question "Wat is het idee en wat zie je in de demonstratie? Geef tijdcodes."
```

Alleen publieke YouTube-links worden ondersteund; geen uploads van lokale of
privébestanden. De vraag en link gaan naar `https://openrouter.ai/api/v1/chat/completions`
en via de expliciet gekozen `google-ai-studio`-provider naar Google. De
standaard is `google/gemini-3.7-flash`, met laag redeneerbudget en maximaal 4096
antwoordtokens. `--model` kan een expliciet gekozen Gemini-model gebruiken.
`--max-tokens` begrenst de aangevraagde uitvoer, geen totaalbedrag of alle
interne redeneertokens. Lange video's kunnen meer kosten; schat die opdracht
vooraf in. Het rapport toont de werkelijk door OpenRouter gemelde kosten in USD,
of expliciet dat ze onbekend zijn. Eén proef voorspelt geen vaste videoprijs.

Credentialvolgorde: `OPENROUTER_API_KEY`, anders `--auth-file`, anders
`OPENROUTER_AUTH_FILE`, anders het bestaande T3-profiel
`~/.config/t3-code/pi-openrouter/auth.json` (`openrouter.key`). De helper leest
alleen de sleutel, kopieert hem niet en schrijft hem niet in rapporten.
Ontbreekt toegang, gebruik de veilige secret-invoer van de harness. Vraag geen
sleutels in gewone chat en zet ze nooit in argumenten of Git.

De API-call heeft standaard 240 seconden timeout (`--timeout` is instelbaar).
Bij een fout of timeout stopt de helper zonder fallback of herhaling. Een
timeout kan alsnog verbruik hebben veroorzaakt. Een afgebroken antwoord blijft
als gedeeltelijk bewijs bewaard met exit 2. Een succesvolle HTTP-call met lege
inhoud geldt niet als een bruikbare analyse. Een vervolgcall hergebruikt geen
Gemini-context; verstuur alleen wanneer het bestaande antwoord niet volstaat.

## Bronnen en onderhoud

- [OpenRouter video-inputs](https://openrouter.ai/docs/guides/overview/multimodal/videos):
  `video_url`, YouTube-ondersteuning en agentic verwerking.
- [OpenRouter providerselectie](https://openrouter.ai/docs/guides/routing/provider-selection):
  vaste provider en uitgeschakelde fallback.
- [yt-dlp](https://github.com/yt-dlp/yt-dlp#usage-and-options) en
  [YouTube JS-runtime](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

De API-vorm en lokale extractie zijn gecontroleerd op 2026-11-13. Bekijk bij een
API- of downloadwijziging de actuele officiële bron; modelnamen en prijzen zijn
geen blijvende garanties. Er is geen upstream `watch`-skill geïnstalleerd of
gekopieerd: de helpers voeren de twee afgesproken routes rechtstreeks uit.
