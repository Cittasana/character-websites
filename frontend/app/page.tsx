/**
 * Landing page — served at the root domain (not a character site).
 * Editorial premium presentation of the Character Websites product.
 */

import Link from "next/link";

const PROCESS_STEPS = [
  {
    n: "01",
    title: "Omi-Recorder erfasst die Person",
    body:
      "Der Nutzer trägt ein Omi-Wearable. Es nimmt im Hintergrund auf — in Meetings, Gesprächen, Gedanken. Keine künstliche „Ich stelle mich jetzt vor“-Session. Das System bekommt echte verbale Daten: Tonalität, Rhythmus, Wortwahl, emotionale Kadenz.",
    stack: ["Omi SDK", "librosa acoustic analysis", "Whisper fallback"],
  },
  {
    n: "02",
    title: "Hive Mind verarbeitet und speichert",
    body:
      "Aufnahmen landen verschlüsselt in Supabase Storage. Celery-Jobs verarbeiten sie asynchron: Transkription, Akustik-Extraktion, dann Claude-Analyse. Das Ergebnis ist ein strukturiertes Persönlichkeits-Schema — 7 Dimensionen plus Persona-Blend-Gewichte — als Vektor-Embedding in pgvector.",
    stack: ["Supabase pgvector", "Celery + Redis", "Claude Sonnet"],
  },
  {
    n: "03",
    title: "Website rendert sich aus der Persönlichkeit",
    body:
      "Das Schema treibt alles: Farben, Typografie, Layout-Dichte, Asymmetrie, Animationen. Vier Kern-Personas — Minimalist-Refined, Maximalist-Bold, Organic-Warm, Structured-Professional — werden gewichtet gemischt. Jede Website ist einzigartig, weil die Persönlichkeit das Design vorschreibt.",
    stack: ["Next.js 14 App Router", "Compositional Persona Blending", "ISR ≤ 60s"],
  },
  {
    n: "04",
    title: "Besucher interagieren mit der echten Person",
    body:
      "Ein Recruiter öffnet cosmo.characterwebsites.com und tippt eine Frage. Das System sucht semantisch in den Transkripten, findet die relevantesten echten Aussagen, und antwortet — synthetisiert in ihrer Stimme. Kein generischer Chatbot. Eine Antwort aus echten Worten.",
    stack: ["Voice Q&A", "Semantic Search via pgvector", "Voice Synthesis"],
  },
];

const USE_CASES = [
  {
    tag: "V1",
    label: "CV Mode",
    body:
      "Bewerbungen und Professional Branding. Hero, Persönlichkeits-Insights, Experience-Timeline, Employer Q&A Widget, Kalender-Booking. Der Recruiter interagiert mit der echten Persönlichkeit des Bewerbers.",
  },
  {
    tag: "V1",
    label: "Dating Mode",
    body:
      "Avatar Gallery, Voice Clips Player mit Web Audio Waveform, Personality Scores für Warmth, Humor, Ambition, Adventure, Values Section. Authentizität statt kuratierter Hochglanz-Profile.",
  },
  {
    tag: "V2",
    label: "Legacy Mode",
    body:
      "Digitales Vermächtnis. Kinder sprechen in 20 Jahren mit dem Hive Mind ihrer Eltern. Die verbale Essenz einer Person bleibt erhalten. Der eigentliche emotionale Kaufgrund.",
  },
];

const HIVE_LAYERS = [
  {
    n: "Schicht 01",
    label: "Operativ — Strukturierte Fakten",
    body: "Relationale Daten, schnell abrufbar, RLS-gesichert. Supabase Postgres.",
    items: [
      "User-Profile, Auth, Subdomains",
      "CV-Daten, Skills, Projekte",
      "Website-Configs, Persona-Gewichte",
      "Audit Logs aller Ingest-Events",
      "Voice Recordings (verschlüsselt, Supabase Storage)",
    ],
  },
  {
    n: "Schicht 02",
    label: "Qualitativ — Verbale Essenz",
    body: "Vektor-Embeddings, semantisch durchsuchbar. pgvector in Supabase.",
    items: [
      "Transkript-Chunks als Embeddings",
      "7-Dimensionen Persönlichkeits-Schema (versioniert)",
      "Akustik-Metadaten: Pitch, Rhythmus, Kadenz",
      "Persona Blend Weights (historisch)",
      "Similarity Search für Voice Q&A",
    ],
  },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-[#fafaf7] text-neutral-900 antialiased selection:bg-neutral-900 selection:text-[#fafaf7]">
      {/* ── Top nav ─────────────────────────────────────────────────────── */}
      <header className="border-b border-neutral-900/10">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-5 md:px-12">
          <div className="flex items-baseline gap-3">
            <span className="text-[13px] font-semibold uppercase tracking-[0.18em]">
              Character Websites
            </span>
            <span className="hidden text-[11px] uppercase tracking-[0.2em] text-neutral-500 md:inline">
              Cittasana AI · 2026
            </span>
          </div>
          <nav className="flex items-center gap-2">
            <Link
              href="/auth/login"
              className="px-3 py-2 text-[13px] font-medium uppercase tracking-[0.14em] text-neutral-700 hover:text-neutral-900"
            >
              Anmelden
            </Link>
            <Link
              href="/auth/register"
              className="bg-neutral-900 px-5 py-2.5 text-[13px] font-medium uppercase tracking-[0.14em] text-[#fafaf7] transition-colors hover:bg-neutral-700"
            >
              Loslegen
            </Link>
          </nav>
        </div>
      </header>

      {/* ── Hero ───────────────────────────────────────────────────────── */}
      <section className="border-b border-neutral-900/10">
        <div className="mx-auto max-w-[1400px] px-6 pt-20 pb-24 md:px-12 md:pt-32 md:pb-40">
          <div className="grid grid-cols-12 gap-6 md:gap-10">
            <div className="col-span-12 md:col-span-2">
              <div className="text-[11px] font-medium uppercase tracking-[0.22em] text-neutral-500">
                Project Brief
              </div>
              <div className="mt-2 text-[11px] uppercase tracking-[0.22em] text-neutral-500">
                V1 · Ready
              </div>
            </div>

            <div className="col-span-12 md:col-span-10">
              <h1 className="font-serif text-[clamp(3rem,9vw,8.5rem)] leading-[0.92] tracking-[-0.04em]">
                Premium Personal
                <br />
                <span className="italic text-neutral-500">Identity Engine.</span>
              </h1>
              <div className="mt-10 grid grid-cols-12 gap-6">
                <p className="col-span-12 max-w-2xl text-[1.15rem] leading-[1.55] text-neutral-700 md:col-span-7 md:text-[1.35rem]">
                  Eine Person spricht — in echten Momenten, ungefiltert — in das
                  Omi-Wearable. Das System hört zu, versteht die verbale Essenz,
                  und baut daraus eine lebendige Online-Präsenz. Keine
                  Templates. Keine Curation. Nur echte Persönlichkeit.
                </p>
                <div className="col-span-12 md:col-span-5 md:border-l md:border-neutral-900/10 md:pl-8">
                  <div className="text-[11px] uppercase tracking-[0.2em] text-neutral-500">
                    Investment
                  </div>
                  <div className="mt-2 font-serif text-4xl tracking-tight">
                    EUR 1.000
                  </div>
                  <div className="mt-1 text-[13px] text-neutral-600">
                    One-Time · keine laufenden Lizenzkosten
                  </div>
                </div>
              </div>

              <div className="mt-12 flex flex-wrap items-center gap-4">
                <Link
                  href="/auth/register"
                  className="bg-neutral-900 px-7 py-4 text-[13px] font-medium uppercase tracking-[0.16em] text-[#fafaf7] transition-colors hover:bg-neutral-700"
                >
                  Persönlichkeit aufnehmen
                </Link>
                <Link
                  href="#prozess"
                  className="border border-neutral-900/20 px-7 py-4 text-[13px] font-medium uppercase tracking-[0.16em] text-neutral-900 transition-colors hover:border-neutral-900"
                >
                  Wie es funktioniert
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Manifesto pull-quote ───────────────────────────────────────── */}
      <section className="border-b border-neutral-900/10 bg-neutral-900 text-[#fafaf7]">
        <div className="mx-auto max-w-[1400px] px-6 py-24 md:px-12 md:py-36">
          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-12 md:col-span-2">
              <div className="text-[11px] uppercase tracking-[0.22em] text-neutral-500">
                Manifest
              </div>
            </div>
            <blockquote className="col-span-12 font-serif text-[clamp(1.75rem,4.5vw,3.75rem)] leading-[1.1] tracking-[-0.02em] md:col-span-10">
              <span className="text-neutral-500">„</span>
              Authenticity over curation — the website grows with{" "}
              <span className="italic">who you actually are,</span> not who you
              want to appear to be.
              <span className="text-neutral-500">&ldquo;</span>
            </blockquote>
          </div>
        </div>
      </section>

      {/* ── Wie es funktioniert ────────────────────────────────────────── */}
      <section id="prozess" className="border-b border-neutral-900/10">
        <div className="mx-auto max-w-[1400px] px-6 py-24 md:px-12 md:py-32">
          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-12 md:col-span-3">
              <div className="text-[11px] uppercase tracking-[0.22em] text-neutral-500">
                Prozess
              </div>
              <h2 className="mt-4 font-serif text-5xl leading-[0.95] tracking-tight md:text-6xl">
                Wie es funktioniert.
              </h2>
            </div>
            <div className="col-span-12 md:col-span-9">
              <ol className="divide-y divide-neutral-900/10 border-y border-neutral-900/10">
                {PROCESS_STEPS.map((step) => (
                  <li
                    key={step.n}
                    className="grid grid-cols-12 gap-4 py-10 md:gap-6 md:py-12"
                  >
                    <div className="col-span-2 md:col-span-1">
                      <div className="font-serif text-3xl text-neutral-400">
                        {step.n}
                      </div>
                    </div>
                    <div className="col-span-10 md:col-span-7">
                      <h3 className="font-serif text-2xl leading-tight md:text-3xl">
                        {step.title}
                      </h3>
                      <p className="mt-3 text-[15px] leading-relaxed text-neutral-700">
                        {step.body}
                      </p>
                    </div>
                    <div className="col-span-12 md:col-span-4">
                      <ul className="space-y-1.5">
                        {step.stack.map((s) => (
                          <li
                            key={s}
                            className="text-[12px] uppercase tracking-[0.14em] text-neutral-500"
                          >
                            — {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </div>
      </section>

      {/* ── Hive Mind Architektur ──────────────────────────────────────── */}
      <section className="border-b border-neutral-900/10 bg-[#f0ede5]">
        <div className="mx-auto max-w-[1400px] px-6 py-24 md:px-12 md:py-32">
          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-12 md:col-span-4">
              <div className="text-[11px] uppercase tracking-[0.22em] text-neutral-500">
                Architektur
              </div>
              <h2 className="mt-4 font-serif text-5xl leading-[0.95] tracking-tight md:text-6xl">
                Hive Mind.
              </h2>
              <p className="mt-6 max-w-sm text-[15px] leading-relaxed text-neutral-700">
                Der Hive Mind ersetzt die klassische Datenbank nicht — er liegt
                darüber. Zwei Schichten plus eine Orchestrierungsebene.
              </p>
            </div>

            <div className="col-span-12 md:col-span-8">
              <div className="grid grid-cols-1 gap-px bg-neutral-900/10 md:grid-cols-2">
                {HIVE_LAYERS.map((layer) => (
                  <div key={layer.n} className="bg-[#f0ede5] p-8">
                    <div className="text-[11px] uppercase tracking-[0.18em] text-neutral-500">
                      {layer.n}
                    </div>
                    <h3 className="mt-2 font-serif text-2xl tracking-tight">
                      {layer.label}
                    </h3>
                    <p className="mt-3 text-[14px] leading-relaxed text-neutral-700">
                      {layer.body}
                    </p>
                    <ul className="mt-6 space-y-2 border-t border-neutral-900/10 pt-4">
                      {layer.items.map((it) => (
                        <li
                          key={it}
                          className="text-[13px] leading-relaxed text-neutral-800"
                        >
                          · {it}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>

              <div className="mt-10 border border-neutral-900/15 bg-[#fafaf7] p-8">
                <div className="flex items-baseline justify-between">
                  <div className="text-[11px] uppercase tracking-[0.18em] text-neutral-500">
                    Orchestrierung
                  </div>
                  <div className="text-[11px] uppercase tracking-[0.18em] text-neutral-500">
                    Celery + Redis · Async Job Queue
                  </div>
                </div>
                <p className="mt-3 font-serif text-2xl leading-snug tracking-tight md:text-[1.75rem]">
                  Omi liefert Audio → Celery transkribiert → librosa extrahiert
                  Akustik → Claude analysiert → pgvector speichert → ISR
                  invalidiert. Unter 60 Sekunden vom Upload bis zur
                  aktualisierten Website.
                </p>
                <ul className="mt-6 grid grid-cols-1 gap-x-8 gap-y-2 sm:grid-cols-2">
                  {[
                    "Upload-Trigger → async Job",
                    "Deduplication via Audio-Hash",
                    "Retry-Logik built-in",
                    "Redis cacht häufige Q&A-Antworten",
                    "Schema-Versionierung (Persönlichkeits-Zeitlinie)",
                    "ISR-Webhook bei Schema-Update",
                  ].map((it) => (
                    <li
                      key={it}
                      className="text-[13px] leading-relaxed text-neutral-700"
                    >
                      — {it}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Use Cases ──────────────────────────────────────────────────── */}
      <section className="border-b border-neutral-900/10">
        <div className="mx-auto max-w-[1400px] px-6 py-24 md:px-12 md:py-32">
          <div className="flex items-end justify-between">
            <div>
              <div className="text-[11px] uppercase tracking-[0.22em] text-neutral-500">
                Anwendungen
              </div>
              <h2 className="mt-4 font-serif text-5xl leading-[0.95] tracking-tight md:text-6xl">
                Drei Modi.
                <br />
                <span className="italic text-neutral-500">Eine Identität.</span>
              </h2>
            </div>
          </div>

          <div className="mt-16 grid grid-cols-1 gap-px bg-neutral-900/10 md:grid-cols-3">
            {USE_CASES.map((uc) => (
              <article key={uc.label} className="bg-[#fafaf7] p-8 md:p-10">
                <div className="flex items-baseline justify-between">
                  <h3 className="font-serif text-3xl tracking-tight">
                    {uc.label}
                  </h3>
                  <span className="border border-neutral-900/20 px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.18em] text-neutral-700">
                    {uc.tag}
                  </span>
                </div>
                <p className="mt-6 text-[14px] leading-relaxed text-neutral-700">
                  {uc.body}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* ── Status ─────────────────────────────────────────────────────── */}
      <section className="border-b border-neutral-900/10">
        <div className="mx-auto max-w-[1400px] px-6 py-24 md:px-12 md:py-28">
          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-12 md:col-span-3">
              <div className="text-[11px] uppercase tracking-[0.22em] text-neutral-500">
                Stand · 2026
              </div>
              <h2 className="mt-4 font-serif text-5xl leading-[0.95] tracking-tight md:text-6xl">
                Projekt&shy;status.
              </h2>
            </div>
            <div className="col-span-12 grid grid-cols-2 gap-px bg-neutral-900/10 md:col-span-9 md:grid-cols-4">
              {[
                { kpi: "15/15", label: "Phasen abgeschlossen" },
                { kpi: "3", label: "Parallel-Teams (Backend · Frontend · Omi)" },
                { kpi: "6/6", label: "Integration Tests grün" },
                { kpi: "≤ 60s", label: "Vom Upload zur Website" },
              ].map((k) => (
                <div key={k.label} className="bg-[#fafaf7] p-8">
                  <div className="font-serif text-5xl tracking-tight">
                    {k.kpi}
                  </div>
                  <div className="mt-3 text-[12px] uppercase tracking-[0.14em] text-neutral-500">
                    {k.label}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-16 grid grid-cols-12 gap-6">
            <div className="col-span-12 md:col-span-6">
              <div className="text-[11px] uppercase tracking-[0.18em] text-neutral-500">
                Sofort — Blocker lösen
              </div>
              <ul className="mt-4 divide-y divide-neutral-900/10 border-y border-neutral-900/10">
                {[
                  "Omi Developer Access beantragen (omi.me/developers)",
                  "Wildcard DNS *.characterwebsites.com → Vercel",
                  "ANTHROPIC_API_KEY + Supabase Keys in Vercel Env",
                  "Supabase Migration: Backend auf supabase-py portieren",
                ].map((it) => (
                  <li
                    key={it}
                    className="py-3 text-[14px] leading-relaxed text-neutral-800"
                  >
                    {it}
                  </li>
                ))}
              </ul>
            </div>
            <div className="col-span-12 md:col-span-6">
              <div className="text-[11px] uppercase tracking-[0.18em] text-neutral-500">
                Hive Mind Upgrade — V1+
              </div>
              <ul className="mt-4 divide-y divide-neutral-900/10 border-y border-neutral-900/10">
                {[
                  "Schema-Versionierung (Persönlichkeits-Zeitlinie)",
                  "Semantic Search aus echten Transkript-Chunks",
                  "Redis Answer Pattern Caching",
                  "Besucher-Kontext-Routing (Recruiter vs. Partner)",
                ].map((it) => (
                  <li
                    key={it}
                    className="py-3 text-[14px] leading-relaxed text-neutral-800"
                  >
                    {it}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── Final CTA ──────────────────────────────────────────────────── */}
      <section className="bg-neutral-900 text-[#fafaf7]">
        <div className="mx-auto max-w-[1400px] px-6 py-28 md:px-12 md:py-40">
          <div className="grid grid-cols-12 gap-6">
            <div className="col-span-12 md:col-span-8">
              <h2 className="font-serif text-[clamp(2.5rem,7vw,6rem)] leading-[0.95] tracking-[-0.03em]">
                Deine Stimme.
                <br />
                <span className="italic text-neutral-500">
                  Deine Persönlichkeit.
                </span>
                <br />
                Deine Website.
              </h2>
            </div>
            <div className="col-span-12 flex flex-col justify-end md:col-span-4">
              <p className="text-[15px] leading-relaxed text-neutral-400">
                Beginne jetzt mit deiner ersten Aufnahme. Dein Hive Mind formt
                sich mit jedem gesprochenen Wort.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  href="/auth/register"
                  className="bg-[#fafaf7] px-7 py-4 text-[13px] font-medium uppercase tracking-[0.16em] text-neutral-900 transition-colors hover:bg-neutral-300"
                >
                  Loslegen
                </Link>
                <Link
                  href="/auth/login"
                  className="border border-[#fafaf7]/30 px-7 py-4 text-[13px] font-medium uppercase tracking-[0.16em] text-[#fafaf7] transition-colors hover:border-[#fafaf7]"
                >
                  Anmelden
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <footer className="border-t border-neutral-900/10 bg-[#fafaf7]">
        <div className="mx-auto flex max-w-[1400px] flex-col gap-3 px-6 py-10 md:flex-row md:items-center md:justify-between md:px-12">
          <div className="text-[12px] uppercase tracking-[0.18em] text-neutral-600">
            Character Websites · Cittasana AI · 2026
          </div>
          <div className="text-[12px] uppercase tracking-[0.18em] text-neutral-500">
            ai.cittasana.de
          </div>
        </div>
      </footer>
    </main>
  );
}
