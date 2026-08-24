# Production Readiness Diff — från dagens Scio till den avsedda kärnprodukten

**Datum:** 2026-08-24  
**Underlag:** `PRODUCTION_READINESS_REVIEW.GPT.md`, `PRODUCTION_READINESS_REVIEW_CLAUDE.md`, aktuell implementation, produktdokumentation och jämförelse med Lovables offentliga funktioner.

## 1. Sammanfattning

Scio är i dag en **tekniskt avancerad utvecklingsalfa**, inte en produktionsklar Lovable-konkurrent.

Den viktigaste slutsatsen är att Scio inte bör försöka vinna genom omedelbar funktionsparitet med Lovable. Den trovärdiga differentieringen är i stället:

> **Scio förstår och formaliserar problemet, skapar en godkänd arkitektur, bygger appen i kontraktsbärande delar och kan därefter förändra minsta korrekta område utan att tappa helheten eller skapa regressioner.**

Den önskade kärnloopen är:

1. Användaren beskriver sitt problem.
2. Scio samlar strukturerade krav och identifierar motsägelser.
3. Scio utformar en genomtänkt lösning och arkitektur.
4. Användaren granskar och godkänner kontraktet.
5. Scio genererar en körbar preview.
6. Användaren markerar element och/eller beskriver en förändring.
7. Scio beräknar minsta beroendemässigt kompletta ändringsyta.
8. Endast godkända paket och filer får förändras.
9. Resultatet verifieras mot krav, design, interfaces, tester och tidigare fungerande beteende.
10. Användaren godkänner och Scio färdigställer appen.
11. Samma kontrollerade ändringsloop fortsätter på den levererade appen.
12. Resultatet är fungerande, testat, begripligt och möjligt för utvecklare att ta över.

Mycket av den konceptuella och tekniska grunden finns. Det som återstår är framför allt att göra hela loopen stabil, säker, mätbar och användbar från början till slut.

---

## 2. Produktens verkliga kärna

Scio är inte i första hand:

- en chatt som skriver filer;
- en visuell hemsidebyggare;
- en hostingplattform;
- en samling AI-modeller;
- en billigare kopia av Lovable.

Scio ska vara:

> **En kontraktsstyrd programvaruproducent som kan bygga och förändra högkvalitativa appar med kontrollerad påverkan och verifierbart resultat.**

### Fem icke förhandlingsbara invariants

1. **Inget byggs utan kontrakt.** Varje funktion ska kunna spåras till ett godkänt krav, ett synligt antagande eller en teknisk nödvändighet.
2. **Ingen förändring utan impact analysis.** Berörda krav, arkitekturnoder, paket, filer och tester ska identifieras innan kod skrivs.
3. **Ingen otillåten diff.** Förändringar utanför den beslutade ytan ska avvisas eller kräva nytt godkännande.
4. **Ingen promotion utan verifiering.** Kod blir aktuell version först när relevanta kontrakt och tester passerat.
5. **Inget dolt misslyckande.** Användaren ska se vad som ändrades, testades, passerade, misslyckades och inte kunde verifieras.

### Viktig precisering

Löftet ska inte vara att bokstavligen endast den markerade komponenten alltid ändras. En förändring kan kräva legitima följdändringar.

Exempel: “Gör telefonnummer obligatoriskt” kan påverka formulär, validering, API, datamodell och tester.

Rätt löfte är:

> **Endast det minsta beroendemässigt kompletta och förklarade området förändras.**

---

## 3. Nuläge

### Redan starkt eller huvudsakligen implementerat

- React-app, NestJS-API, Python-engine och PostgreSQL-datamodell.
- Clerk-auth och workspacebaserad tenantmodell.
- Projekt-, spec-, design-, build job- och build version-livscykel.
- Strukturerad intake och typad specifikation.
- “The whole” som bestående helhetskontrakt.
- Layer B: förståelse, arkitekturgraf och generation playbook.
- Layer C: dependency-ordnade, kontraktsbärande byggpaket.
- Preview och visuella markeringar kopplade till `data-scio-id` och paket.
- Directed regeneration med fil-/paketavgränsning.
- Versionshistorik och icke-destruktiv restore.
- BuildJob, cancellation, idempotens och kostnadsmätning.
- Modellrelay, flera pass och per-build-budget.
- Verifierings- och instrumentationgrindar.
- Komponentbibliotek med matchning, assembly och contribution-back.
- Fresh-clone-CI och omfattande testkod.
- Flera fail-closed-skydd för auth, engine-token och sandboxval.

### Övergripande kvalitetsbedömning

| Område | Nuläge |
|---|---|
| Produktidé | Stark och tydligt differentierbar |
| Arkitektur | Genomtänkt och ovanligt mogen för fasen |
| Kodstruktur | Bra till mycket bra |
| Datamodell | Stark, med databas-enforcerade invariants |
| Testdesign | Bred och lovande, men inte verifierad i aktuell miljö |
| Kärnflöde | Till stor del implementerat, inte tillräckligt runtime-bevisat |
| Riktad regenerering | Teknisk grund finns, behöver hårdare bevis |
| Genererad appkvalitet | Ambition och mekanismer finns, resultatet är inte empiriskt bevisat |
| Säkerhet | Bra grund men produktionsblockerande luckor |
| Drift | Omoget; största gapet |
| Lovable-paritet | Långt ifrån i plattformsbredd |

---

## 4. Gap mellan nuläge och önskad kärna

| Förmåga | Nuläge | Önskat slutläge | Gap | Prioritet |
|---|---|---|---|---|
| Kravinsamling | Strukturerad intake finns | Stabil dialog som täcker relevanta krav utan onödig friktion | Verifiera med riktiga användare och varierade appar | P1 |
| Godkänt kontrakt | Spec/whole finns | All kod och alla ändringar är spårbara till kontrakt | Full traceability och användarvänlig diff saknas | P1 |
| Arkitekturval | Layer B skapar arkitekturgraf | Kvalitetsmotiverad arkitektur med synliga trade-offs | Behöver benchmark och utvecklargranskning | P1 |
| Paketindelning | Layer C finns | Stabil ownership, interfaces och beroendegraf | Behöver valideras på större/långlivade appar | P1 |
| Preview | Körbar preview finns lokalt | Säker, pålitlig och delbar preview | Produktionssandbox/deployment saknas | P1 |
| Elementkoppling | ID/package-instrumentation finns | Stabil identitet över generationer och refaktoreringar | Stabilitet och coverage måste mätas | P1 |
| Impact analysis | Paket och markeringsdata finns | Deterministisk minimal dependency closure före ändring | Behöver formaliseras som explicit plan/gate | P1 |
| Begränsad regenerering | Directed change finns | Otillåtna filändringar omöjliga; avvikelse kräver godkännande | Behöver hård write-boundary och regressionstest | P1 |
| Verifiering | Flera lokala grindar finns | Pakettest + konsumenttest + browserflöde + säkerhet + global smoke | Beviskedjan behöver förenas och visas | P1 |
| Atomic promotion | Versioner/restore finns | Endast komplett verifierad change set blir current | Behöver transaktionell promotion och rollbacktest | P1 |
| Resultatrapport | Honest status finns | Krav-, test-, säkerhets- och diffbevis i Reveal | UI och datakorrelation är ofullständiga | P1 |
| Kodkvalitet | Playbook och fixed stack finns | Utvecklare föredrar koden i blind jämförelse | Extern evidens saknas | P1 |
| Bibliotek | Första catalog/assembly/contribution finns | Brett, kuraterat och juridiskt säkert featurebibliotek | Liten katalog, quality signals ofullständiga | P2 |
| Kostnad | Estimat, tak och ledger finns | Förutsägbart estimat och atomisk reservation | Race och fel spend-korrelation finns | P2 |
| Export | Git finns internt i workspace | Download och GitHub/GitLab-handoff | Produktfunktion saknas | P1 |
| Publicering | Inte implementerat | Delbar live-URL med rollback | Saknas | P1 |

---

## 5. Kritiska fel som måste rättas innan kärnan kan anses pålitlig

### 5.1 Tenantkontroll före idempotensreplay

Buildreplay kan i nuläget ske innan projektägarskap verifieras. Detta bryter en grundläggande säkerhetsinvariant även om nyckeln är svår att gissa.

**Krav:** varje replay måste först verifiera projektets workspaceägarskap, med regressionstest mot riktig Prisma/PostgreSQL.

### 5.2 Heartbeat och reaper är inte sammanhängande

Engine skickar keepalive-kommentarer under långa tysta steg, men de uppdaterar inte jobbets persistenta heartbeat. Ett aktivt bygge kan därför markeras som dött och ett andra bygge startas mot samma workspace.

**Krav:** separat lease/heartbeat som lever under hela arbetet och förhindrar att två ägare skriver i samma workspace.

### 5.3 Långjobb ägs av HTTP-requesten

BuildJob är persistent men exekveringen är fortfarande inline i API-processen.

**Krav för robust produkt:** durabel kö, separat worker, lease, idempotent retry, cancellation och eventlogg som SSE kan läsa.

### 5.4 Verifieringsbeviset är fragmenterat

Tester, instrumentation, typecheck, browserobservation och honest status finns i olika delar, men användaren får ännu inte ett komplett bevis för varje förändring.

**Krav:** ett sammanhållet `VerificationReport` kopplat till change/build-version.

### 5.5 Produktionssandbox saknas

ACA-providern är en stub och Docker saknar default-deny-egress.

**Krav:** isolerad produktionsprovider med verifierade nätverks-, resurs-, filsystems- och teardown-egenskaper.

---

## 6. Definition av “endast det markerade påverkas”

För varje förändring bör Scio producera en maskinläsbar change plan:

```text
User intent
  -> selected element ids / semantic prompt
  -> owning packages
  -> affected contracts
  -> transitive dependency closure
  -> allowed files and operations
  -> required tests
  -> expected invariants
  -> explicit approval if scope expands
```

Efter generation ska följande gälla:

- varje ändrad fil finns i change plans allow-list;
- varje ändring kan motiveras av ett påverkat kontrakt;
- publika interfaces ändras endast om planen tillåter det;
- orelaterade filer är identiska;
- berörda paket passerar egna tester;
- beroende konsumenter passerar kontraktstester;
- centrala globala flöden passerar smoke tests;
- element-id och package mapping är intakta;
- aktuell version flyttas först efter godkänd verifiering;
- ett misslyckande lämnar föregående version orörd.

### Exempel på förändringsrapport

```text
Begäran: Gör telefonnummer obligatoriskt i bokningen

Direkt påverkat:
- booking-form

Beroende påverkan:
- booking-contract
- booking-api
- booking-schema
- booking-confirmation

Ändrade filer: 5
Verifierat oförändrade filer: 61
Kontrakt: 7/7 godkända
Tester: 18/18 passerade
Browserflöden: 3/3 passerade
Säkerhetskontroller: 4/4 passerade
Resultat: redo för användarens godkännande
```

---

## 7. Kvalitetsdefinition för genererade appar

“Väldigt hög kvalitet” måste vara mätbart. En app bör inte betraktas som färdig enbart för att den kompilerar och renderar.

### Funktionell kvalitet

- Alla godkända krav har en implementation eller tydligt blockerad status.
- Centrala användarflöden har körts i browser.
- Data skrivs, läses och isoleras korrekt.
- Fel-, loading- och empty states fungerar.

### Kodkvalitet

- Tydliga paketgränser och interfaces.
- Ingen duplicerad eller död kod.
- Begränsad komplexitet.
- Typkontroll och lint passerar.
- Utvecklare kan förstå och modifiera resultatet utan Scio.

### Testkvalitet

- Enhetstester för affärsregler.
- Komponenttester för viktig UI-logik.
- Integrationstester för data/auth/API.
- Browsertester för kritiska användarresor.
- Regressionstester skapas när ett fel rättas.

### Säkerhetskvalitet

- AuthN och authZ verifierade.
- RLS/dataisolering testad.
- Inputs validerade.
- Secrets ligger utanför klientkod.
- Dependency- och kodscan genomförda.
- Inga kritiska fynd före leverans.

### UX-kvalitet

- Responsiv layout.
- Tangentbordsanvändning och grundläggande accessibility.
- Stabil navigation.
- Tydlig feedback och felhantering.
- Lighthouse-/accessibilityresultat redovisas där de är relevanta.

### Leveransbevis

Reveal bör visa:

- krav uppfyllda/ej uppfyllda;
- tester och browserflöden;
- säkerhetskontroller;
- ändrade paket/filer;
- verifierat oförändrad yta;
- modell-/byggkostnad;
- byggtid;
- kvarvarande risker;
- versions-id och exportmöjlighet.

---

## 8. Lovables bibliotek och Scios möjliga fördel

Lovable har offentligt dokumenterat flera former av återanvändning:

1. **Design systems:** versionshanterade React-komponenter, tokens, schema, regler, setup verification och adherence checks.
2. **Managed registry:** privat npm-register för komponenter, utilities och interna SDK:er.
3. **Cross-project referencing:** återanvändning av komponenter, layouts, authflöden, integrationer, features, assets och chatthistorik från andra projekt i samma workspace.
4. **Remix/templates:** kopiera ett projekt som startpunkt.

Detta betyder att “vi har ett komponentbibliotek” inte i sig är en tillräcklig differentierare.

### Vad som inte är offentligt belagt hos Lovable

Det finns ingen offentlig dokumentation som visar samma kompletta mekanism som Scio avser:

- automatiskt bidrag från varje lyckat bygge;
- generalisering bort från projektspecifika begrepp;
- omverifiering efter generalisering;
- kontraktsbaserad automatisk matchning före generation;
- kvalitetsbevis per återanvänd feature;
- Pareto-baserad ersättning av äldre implementationer;
- automatisk assembly som förstahandsval och generation som fallback.

Lovable kan ha interna system som inte är offentliga. Därför går det inte att hävda att de saknar intern återanvändning eller lärande. Den verifierbara skillnaden är att deras publika produkt främst erbjuder användarstyrda design systems, paket, templates och projektreferenser.

### Scios möjliga biblioteksfördel

Scios bibliotek kan bli en fördel om det är:

- featurebaserat, inte bara visuellt;
- kontraktsmatchat;
- testat och säkerhetsgranskat;
- automatiskt anpassningsbart;
- mätbart bättre efter varje version;
- juridiskt och tekniskt säkert mellan tenants;
- billigare än ny generation;
- transparent för användaren.

Biblioteket är dock en förstärkare, inte förutsättningen för att bevisa kärnan. Kärnloopen måste fungera väl även när allt behöver genereras.

---

## 9. Vad Scio inte ska försöka matcha först

Lovable ligger långt före inom:

- hosting och custom domains;
- managed backend;
- GitHub/GitLab-synk;
- collaboration och kommentarer;
- betalningar;
- connector-katalog och MCP;
- mobil- och desktopåtkomst;
- enterprise SSO/SCIM/governance;
- compliance och etablerad drift;
- support och distribution.

Att bygga full paritet innan kärnan är bevisad är sannolikt fel strategi.

Följande kan vänta:

- avancerad collaboration;
- stor connector-katalog;
- inbyggd betalningsplattform;
- enterprisefunktioner;
- automation-builder;
- full website-builder;
- egen komplett managed cloud;
- många templates.

---

## 10. Minsta produkt som bevisar Scio

En extern användare ska kunna:

1. skapa en datadriven app;
2. genomföra kravdialogen;
3. granska och korrigera spec/whole;
4. se föreslagen arkitektur och viktiga trade-offs;
5. godkänna planen;
6. få en riktig körbar preview;
7. markera ett eller flera element;
8. begära både visuell och funktionell förändring;
9. se planerad impact innan större scopeexpansion;
10. få endast det minsta korrekta området ombyggt;
11. se verifieringsbevis och diff;
12. återställa tidigare version;
13. ladda ned koden;
14. öppna en delbar, säker liveversion.

### Rekommenderad första appkategori

Fokusera på datadrivna verksamhetsappar:

- bokning;
- enkelt CRM;
- medlemshantering;
- ärendehantering;
- kundportal;
- inventarie-/orderadministration.

Dessa gör det möjligt att testa UI, data, auth, roller, affärsregler, ändringar och regressionsskydd utan att först lösa varje möjlig produkttyp.

---

## 11. Saknade funktioner — prioriterade efter kärnans behov

### Måste finnas för att bevisa kärnan

- Rättningar för tenantreplay och heartbeat/reaper.
- Stabil riktig modellkörning på aktuell revision.
- Säker och reproducerbar sandbox.
- Formell impact analysis och change plan.
- Hård fil-/paket-write-boundary.
- Sammanhängande verifieringsrapport.
- Regressionstest för berörda och beroende paket.
- Browserverifiering av centrala flöden.
- Stabil ID-mappning över flera förändringar.
- Atomic promotion och rollback.
- Koddownload.
- Enkel delbar deployment.

### Måste finnas före publik produkt

- Produktionsimages och IaC.
- Default-deny-egress.
- Queue/worker/lease.
- Readiness och graceful shutdown.
- Metrics, tracing, correlation-id och larm.
- Kryptografisk webhookverifiering.
- Runtime-validering och payloadgränser.
- Konto-/workspace-radering och retention.
- CSP, security headers och iframe-sandbox.
- Backup/PITR och restoreövning.
- Dependency audit, SAST, secret scan och SBOM.

### Kan komma efter att kärnan är bevisad

- GitHub/GitLab tvåvägssynk.
- Custom domains och avancerad publiceringskontroll.
- Samarbete, kommentarer och detaljerade roller.
- Betalningar.
- Connector-katalog och MCP.
- Managed backend-UI.
- Website- och automation-lägen.
- Enterprise SSO/SCIM/compliancefunktioner.

---

## 12. Rekommenderad genomförandeordning

### Etapp A — gör kärnan korrekt

1. Rätta tenantreplay.
2. Rätta heartbeat/lease.
3. Definiera och implementera `ChangePlan`.
4. Enforca allowed package/file set.
5. Definiera `VerificationReport`.
6. Gör promotion atomisk och rollbackbar.
7. Lägg regressionstester för samtliga invariants.

### Etapp B — bevisa kärnan

1. Välj 5–10 representativa verksamhetsappar.
2. Bygg dem med riktiga modeller.
3. Gör 10–20 förändringar per app.
4. Mät ändringsyta, regressioner, kostnad, tid och testresultat.
5. Låt externa utvecklare blindgranska koden.
6. Jämför samma uppgifter med Lovable.

### Etapp C — gör den användbar externt

1. Säker stagingdeployment.
2. Isolerad sandbox.
3. Koddownload.
4. Enkel publish/live-URL.
5. Grundläggande observability och operatörsverktyg.
6. Begränsad extern alfa.

### Etapp D — skala endast bevisad efterfrågan

1. Git-synk.
2. Backend-/secretshantering.
3. Integrationer.
4. Collaboration.
5. Betalningar.
6. Enterprisefunktioner.

---

## 13. Hur framgång ska mätas

Scio bör jämföras med Lovable på samma appar och samma förändringar.

| Mått | Önskad signal |
|---|---|
| Kravuppfyllelse | Minst lika hög som Lovable |
| Regressioner efter ändring | Tydligt färre |
| Otillåtna filändringar | Noll |
| Förändrad kodmängd | Mindre och bättre motiverad |
| Testad funktionalitet | Högre verifierad andel |
| Säkerhetsfel | Färre eller tidigare upptäckta |
| ID-stabilitet | Stabil över återkommande ändringar |
| Build/change-kostnad | Förutsägbar och fallande med återanvändning |
| Utvecklarbedömning | Scio-kod föredras i blind review |
| Handoff | Projektet kan köras och ändras utan Scio |
| Användarförtroende | Användaren förstår exakt vad som fungerar |

### Exempel på exitkriterier för kärnan

- Minst fem realistiska appar byggda end-to-end.
- Minst tio efterföljande förändringar per app.
- Noll otillåtna filändringar i accepterade förändringar.
- Alla kritiska användarflöden browserverifierade.
- Inga P1-säkerhets- eller concurrencyfel kvar.
- En extern utvecklare kan ta över varje projekt.
- Majoriteten av blindgranskare föredrar Scio-resultatet framför jämförelseresultatet.
- Minst några externa användare vill fortsätta använda eller betala för tjänsten.

---

## 14. Fortsätta eller stoppa?

### Skäl att fortsätta

- Den svåra delen av produktidén har verklig implementation, inte bara presentation.
- Kombinationen kontrakt, arkitekturgraf, paket, ID-koppling och avgränsad regenerering är fortfarande differentierbar.
- Marknaden har ett kvarvarande problem med regressioner, teknisk skuld och förlorad kontext i AI-genererade appar.
- Scio behöver inte slå Lovable i bredd för att skapa värde.

### Skäl att stoppa eller ändra riktning

- Om användare konsekvent upplever kravsteget som hinder och hoppar över det.
- Om directed regeneration inte ger märkbart färre regressioner.
- Om utvecklare inte föredrar resultatet.
- Om kvaliteten bara är bättre i intern arkitektur men inte i fungerande produkt.
- Om kostnad och tid blir väsentligt högre utan motsvarande kvalitetsvärde.
- Om varje realistiskt bygge kräver manuell räddning.

### Rekommendation

**Fortsätt, men som ett tidsbegränsat valideringsprogram — inte som ett obegränsat försök att bygga full Lovable-paritet.**

Nästa avgörande milstolpe är:

> **En extern användare ska kunna skapa, ändra och leverera en riktig app där Scio kan bevisa att förändringarna var minimala, korrekta och regressionsfria.**

Om Scio kan visa det finns en verklig produkt och en möjlig konkurrensfördel. Om det inte kan visas bör arkitekturen eller positioneringen omprövas innan mer plattformsbredd byggs.

---

## 15. Slutlig riktning

Den mest trovärdiga positioneringen är inte:

> “En ny Lovable med samma funktioner.”

Den är:

> **“AI-appbyggaren för appar som ska överleva prototypstadiet: godkända krav, genomtänkt arkitektur, kontrollerade förändringar och verifierbar kvalitet.”**

Det kortsiktiga målet är inte att hinna ikapp Lovable. Det är att bevisa att Scio kan göra en värdefull sak märkbart bättre:

> **Bygga och förändra riktiga appar utan att helheten, kvaliteten eller utvecklarens förtroende går förlorat.**
