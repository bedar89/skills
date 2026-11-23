# Bedars skillcollectie

Dit is Bedars persoonlijke collectie. Alle actieve skills staan direct onder
`skills/<naam>/`. De README vermeldt de upstreambronnen. Skills worden
handmatig onderhouden en aangepast aan Bedars werkwijze.
Er zijn geen vendorbomen, automatische imports of upstream-updaters.

## Werk aan de collectie

- Lees de betrokken skill en zijn verwijzingen voordat je iets wijzigt.
- Beperk wijzigingen aan externe skills tot de opdracht. Behoud de
  auteursvermeldingen en licenties; voeg geen algemeen beleid toe.
- Houd mapnaam en de `name` in frontmatter gelijk. Voeg alleen een nieuwe skill
  toe als Bedar die heeft gevraagd.
- Behoud benodigde referenties, scripts, assets en auteursvermeldingen.
- Controleer bij verplaatsen, hernoemen of verwijderen ook de aanroepende skills.
- Geef iedere skill de ruimte voor zijn eigen taak. Maak geen nieuwe algemene
  workflow, verplichte reviewronde of extra installatievereiste zonder aanleiding.
- Modelkeuze en rolbezetting staan in de betrokken skill en volgen de opdracht.
  Skillinstructies veranderen geen clientmodelinstellingen.
- Gebruik alleen `AGENTS.md` voor repo-instructies. Maak geen `CLAUDE.md` aan.

## Installatie en controle

Er is geen collectie-installer. Codex leest de geplaatste skillmappen of
directorykoppelingen. Respecteer andere geïnstalleerde skills en bestaande
clientinstellingen. Stop bij een conflict voordat iets wordt overschreven.

Controleer de echte gewijzigde route. Controleer bij documentatieveranderingen
de verwijzingen en aanroepende skills. Voer bij een gewijzigde helper de passende
controles uit. De bestaande CI controleert skillnamen, beschrijvingen en lokale
bestandslinks en draait helpertests en een TypeScript-check. Verander bij
CI-aanpassingen de bestaande vereiste checknamen niet zonder de bijbehorende
branchbescherming mee te nemen.

Een groene CI bewijst geen agentgedrag, modelbeschikbaarheid, werkende externe
URLs of Windows-gedrag. Controleer wat de wijziging raakt en benoem ontbrekend
bewijs. Bewaar credentials en onderzoeksuitvoer buiten Git.

Schrijf kort en duidelijk. Werk README-links bij wanneer de collectie verandert.
Commit, push, publiceer, merge en wijzig andere machines alleen op verzoek.
