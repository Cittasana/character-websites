import Image from "next/image";
import Link from "next/link";
import { Waveform } from "./_landing/Waveform";

const VOICES = [
  {
    name: "Mariama Diallo-Ferreira",
    role: "Architektin · Lissabon",
    tone: "leise, präzise, oft halblachend",
    quote:
      "Ich rede mit meinen Bauplänen, ehrlich. Ich frage sie, was sie wollen. Das klingt verrückt, ich weiß. Aber dann antworten sie tatsächlich.",
    accent: "rgba(180, 90, 60, 0.9)",
  },
  {
    name: "Söhnke Brüggemann",
    role: "Cellist · Hamburg",
    tone: "ruhig, mit kurzen Pausen vor wichtigen Wörtern",
    quote:
      "Eine Website ist auch nur ein Instrument. Sie muss gestimmt sein. Wenn das Holz nicht zu mir gehört, höre ich es sofort.",
    accent: "rgba(110, 96, 80, 0.9)",
  },
  {
    name: "Yuki Tanaka-Holm",
    role: "Strategin · Kopenhagen",
    tone: "schnell denkend, abrupte Wendungen, warmes Lachen",
    quote:
      "Ich will nicht, dass sie meinen Lebenslauf lesen. Ich will, dass sie hören, wie ich denke — auch wenn ich gerade falsch denke.",
    accent: "rgba(70, 90, 70, 0.9)",
  },
];

const MOMENTS = [
  {
    label: "Eine Stimme",
    body:
      "Du sprichst — beim Kaffee, im Auto, beim Spazieren. Nicht in ein Mikro. Einfach so. Das kleine Gerät hört zu.",
  },
  {
    label: "Eine Form",
    body:
      "Aus deinem Tonfall, deinen Pausen, deiner Wortwahl entsteht eine eigene Gestalt — Farben, Schriften, Rhythmus. Niemand sonst klingt wie du.",
  },
  {
    label: "Ein Ort",
    body:
      "Eine Webseite, die nicht aussieht wie du sie haben willst, sondern wie du tatsächlich klingst, wenn keiner zuschaut.",
  },
  {
    label: "Eine Begegnung",
    body:
      "Wenn jemand sie öffnet, spricht sie mit deiner Stimme zurück. Mit Worten, die du wirklich gesagt hast. Nicht synthetisch. Ehrlich.",
  },
];

const MODES = [
  {
    badge: "Bewerbung",
    title: "Wer du beruflich bist.",
    body:
      "Eine ruhige Seite, die deine Gedanken zeigt — nicht deine Buzzwords. Recruiter stellen Fragen, deine Stimme antwortet.",
    palette: ["#1c1410", "#b45a3c", "#e8dccb"],
    sample: {
      label: "CV · Mariama",
      lines: ["Wie löst sie Konflikte im Team?", "Was war 2023 die schwierigste Entscheidung?"],
    },
  },
  {
    badge: "Begegnung",
    title: "Wer du privat bist.",
    body:
      "Statt Hochglanz-Profil-Fotos und Bullet-Points: deine echten Momente. Ein Sprachclip, ein Gedanke, ein Lachen.",
    palette: ["#2a1f1a", "#c97350", "#f0ebe0"],
    sample: {
      label: "Begegnung · Söhnke",
      lines: ["Hört Bach, kocht improvisierend.", "Sucht jemanden, der Stille aushält."],
    },
  },
  {
    badge: "Vermächtnis",
    title: "Wer du bleibst.",
    body:
      "Eines Tages wird jemand mit dir sprechen wollen, der dich nicht mehr fragen kann. Diese Seite weiß noch, wie du klangst.",
    palette: ["#15110d", "#7a6a55", "#ddd2bf"],
    sample: {
      label: "Vermächtnis · Yuki",
      lines: [
        '„Erzähl mir, wie sie über Mut sprach."',
        "47 Stunden Aufnahmen · 2024–2031",
      ],
    },
  },
];

export default function LandingPage() {
  return (
    <main className="min-h-[100dvh] bg-[#faf7f2] text-[#1c1410] antialiased selection:bg-[#1c1410] selection:text-[#faf7f2]">
      {/* Subtle grain — fixed, no GPU repaint on scroll */}
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 z-50 opacity-[0.025] mix-blend-multiply"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>\")",
        }}
      />

      <TopBar />

      <Hero />

      <Pullquote />

      <Voices />

      <FourMoments />

      <SoundSection />

      <Modes />

      <DeviceSection />

      <FinalCTA />

      <Footer />
    </main>
  );
}

/* ─────────────────────────────────────────────────────────────────────────── */

function TopBar() {
  return (
    <header className="border-b border-[#1c1410]/10">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-5 md:px-12">
        <Link href="/" className="flex items-baseline gap-3">
          <span className="font-editorial text-[18px] tracking-tight">
            Character Works
          </span>
          <span className="hidden font-mono text-[10px] uppercase tracking-[0.2em] text-[#1c1410]/50 md:inline">
            seit 2026
          </span>
        </Link>
        <nav className="flex items-center gap-1">
          <Link
            href="#stimmen"
            className="hidden px-3 py-2 text-[13px] text-[#1c1410]/70 transition hover:text-[#1c1410] md:inline-flex"
          >
            Drei Stimmen
          </Link>
          <Link
            href="#momente"
            className="hidden px-3 py-2 text-[13px] text-[#1c1410]/70 transition hover:text-[#1c1410] md:inline-flex"
          >
            Wie es entsteht
          </Link>
          <Link
            href="#modi"
            className="hidden px-3 py-2 text-[13px] text-[#1c1410]/70 transition hover:text-[#1c1410] md:inline-flex"
          >
            Drei Räume
          </Link>
          <Link
            href="/auth/login"
            className="ml-2 px-3 py-2 text-[13px] text-[#1c1410]/70 transition hover:text-[#1c1410]"
          >
            Anmelden
          </Link>
          <Link
            href="/auth/register"
            className="ml-1 rounded-full bg-[#1c1410] px-5 py-2.5 text-[13px] font-medium text-[#faf7f2] transition hover:bg-[#3a2a20] active:translate-y-[1px]"
          >
            Anfangen
          </Link>
        </nav>
      </div>
    </header>
  );
}

/* ─────────────────────────────────────────────────────────────────────────── */

function Hero() {
  return (
    <section className="border-b border-[#1c1410]/10">
      <div className="mx-auto grid max-w-[1400px] grid-cols-12 gap-6 px-6 pb-20 pt-16 md:gap-10 md:px-12 md:pb-32 md:pt-24">
        <div className="col-span-12 flex flex-col justify-end lg:col-span-5">
          <p className="mb-8 inline-flex items-center gap-2 self-start font-mono text-[11px] uppercase tracking-[0.2em] text-[#1c1410]/55">
            <span className="size-1 rounded-full bg-[#b45a3c]" />
            Eine ruhige Einladung
          </p>

          <h1 className="font-editorial text-[clamp(3rem,8vw,6.5rem)] font-light leading-[0.95] tracking-[-0.025em]">
            Eine Webseite,
            <br />
            die
            <span className="italic text-[#b45a3c]"> klingt</span>
            <br />
            wie du.
          </h1>

          <p className="mt-10 max-w-[42ch] text-[17px] leading-[1.65] text-[#1c1410]/75 md:text-[18.5px]">
            Die meisten Online-Profile zeigen, wer wir sein wollen. Diese hier
            zeigt, wer wir tatsächlich sind — in echten Worten, in echten
            Pausen, mit echtem Atem dazwischen.
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-4">
            <Link
              href="/auth/register"
              className="group inline-flex items-center gap-3 rounded-full bg-[#1c1410] px-6 py-3.5 text-[14px] font-medium text-[#faf7f2] transition hover:bg-[#3a2a20] active:translate-y-[1px]"
            >
              Eine Stimme aufnehmen
              <span className="font-mono text-[11px] tracking-wide text-[#faf7f2]/70 transition group-hover:translate-x-0.5">
                →
              </span>
            </Link>
            <Link
              href="#stimmen"
              className="text-[14px] text-[#1c1410]/70 underline-offset-4 transition hover:text-[#1c1410] hover:underline"
            >
              Erst mal still zuhören
            </Link>
          </div>
        </div>

        <figure className="col-span-12 lg:col-span-7">
          <div className="relative aspect-[16/10] w-full overflow-hidden rounded-sm bg-[#1c1410]/5">
            <Image
              src="/landing/hero-listening.jpg"
              alt="Eine Frau sitzt am Fenster im warmen Nachmittagslicht, hält ein kleines Aufnahmegerät in der Hand."
              fill
              priority
              sizes="(min-width: 1024px) 800px, 100vw"
              className="object-cover"
            />
          </div>
          <figcaption className="mt-4 flex items-baseline justify-between font-mono text-[11px] uppercase tracking-[0.18em] text-[#1c1410]/55">
            <span>Mariama · Donnerstag, 16:42</span>
            <span>Ohne Mikrofon. Ohne Skript.</span>
          </figcaption>
        </figure>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────────────── */

function Pullquote() {
  return (
    <section className="bg-[#1c1410] text-[#faf7f2]">
      <div className="mx-auto max-w-[1400px] px-6 py-24 md:px-12 md:py-32">
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-12 md:col-span-2">
            <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-[#faf7f2]/45">
              Worum es geht
            </p>
          </div>
          <blockquote className="col-span-12 md:col-span-10">
            <p className="font-editorial text-[clamp(1.75rem,4vw,3.5rem)] font-light leading-[1.18] tracking-[-0.015em]">
              Ein Lebenslauf erzählt, was du gemacht hast.
              <br />
              Diese Seite hört, wie du es{" "}
              <span className="italic text-[#d99878]">gemeint</span> hast.
            </p>
            <footer className="mt-10 flex items-center gap-4 font-mono text-[11px] uppercase tracking-[0.18em] text-[#faf7f2]/50">
              <span className="block h-px w-10 bg-[#faf7f2]/30" />
              Character Works · ein Versuch
            </footer>
          </blockquote>
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────────────── */

function Voices() {
  return (
    <section id="stimmen" className="border-b border-[#1c1410]/10">
      <div className="mx-auto max-w-[1400px] px-6 py-24 md:px-12 md:py-32">
        <header className="mb-12 grid grid-cols-12 gap-6 md:mb-16">
          <div className="col-span-12 md:col-span-3">
            <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-[#1c1410]/55">
              Drei Stimmen
            </p>
          </div>
          <div className="col-span-12 md:col-span-9">
            <h2 className="font-editorial text-[clamp(2rem,5vw,3.75rem)] font-light leading-[1.05] tracking-[-0.015em]">
              Wir haben drei Menschen
              <br />
              eine Woche lang
              <span className="italic text-[#1c1410]/55"> einfach zugehört</span>.
            </h2>
            <p className="mt-6 max-w-[58ch] text-[16px] leading-[1.65] text-[#1c1410]/70">
              Sie haben nichts vorbereitet. Keine Statements aufgesagt. Sie
              haben gekocht, telefoniert, sich beschwert, gelacht, etwas
              vergessen. Die Seiten, die daraus entstanden sind, klingen nach
              ihnen — nicht nach uns.
            </p>
          </div>
        </header>

        <figure className="relative">
          <div className="relative aspect-[24/11] w-full overflow-hidden rounded-sm bg-[#1c1410]/5">
            <Image
              src="/landing/three-personas.jpg"
              alt="Triptychon dreier Menschen in ihren Arbeits- und Lebensräumen — eine Architektin, ein Cellist, eine Strategin."
              fill
              sizes="(min-width: 1024px) 1300px, 100vw"
              className="object-cover"
            />
          </div>
          <figcaption className="mt-3 font-mono text-[11px] uppercase tracking-[0.18em] text-[#1c1410]/55">
            Mariama · Söhnke · Yuki — drei Räume, drei Stimmen, drei Webseiten.
          </figcaption>
        </figure>

        <div className="mt-16 grid grid-cols-12 gap-x-8 gap-y-12 md:mt-20">
          {VOICES.map((voice) => (
            <article
              key={voice.name}
              className="col-span-12 md:col-span-4 md:border-l md:border-[#1c1410]/10 md:pl-6"
            >
              <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-[#1c1410]/55">
                {voice.role}
              </p>
              <h3 className="mt-2 font-editorial text-[26px] leading-tight tracking-tight">
                {voice.name}
              </h3>
              <p
                className="mt-2 font-editorial text-[14px] italic leading-snug"
                style={{ color: voice.accent }}
              >
                Tonfall: {voice.tone}
              </p>
              <p className="mt-6 font-editorial text-[19px] font-light leading-[1.45] text-[#1c1410]/85">
                <span className="text-[#1c1410]/40">&bdquo;</span>
                {voice.quote}
                <span className="text-[#1c1410]/40">&ldquo;</span>
              </p>
              <Waveform
                className="mt-8 h-6 w-full text-[#1c1410]/35"
                bars={84}
                seed={voice.name.length * 31}
              />
              <p className="mt-3 font-mono text-[10px] tabular-nums text-[#1c1410]/50">
                Aufnahme · 02:47 · 47.2 % der ungefilterten Probe
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────────────── */

function FourMoments() {
  return (
    <section
      id="momente"
      className="border-b border-[#1c1410]/10 bg-[#f0ebe0]"
    >
      <div className="mx-auto max-w-[1400px] px-6 py-24 md:px-12 md:py-32">
        <header className="mb-16 grid grid-cols-12 gap-6 md:mb-24">
          <div className="col-span-12 md:col-span-4">
            <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-[#1c1410]/55">
              Wie es entsteht
            </p>
            <h2 className="mt-4 font-editorial text-[clamp(2rem,4.5vw,3.5rem)] font-light leading-[1.05] tracking-[-0.015em]">
              Vier Momente.
              <br />
              <span className="italic text-[#b45a3c]">Mehr nicht.</span>
            </h2>
          </div>
          <p className="col-span-12 max-w-[48ch] text-[16px] leading-[1.7] text-[#1c1410]/70 md:col-span-7 md:col-start-6">
            Wir haben uns gegen alles entschieden, was nach Software klingt.
            Keine Dashboards, keine Schritte, keine Fortschrittsbalken. Nur das
            hier, in der Reihenfolge, in der es passiert:
          </p>
        </header>

        <ol className="grid grid-cols-12 gap-x-6 gap-y-12">
          {MOMENTS.map((moment, idx) => (
            <li
              key={moment.label}
              className="col-span-12 md:col-span-6 lg:col-span-3"
            >
              <div className="flex items-baseline gap-3">
                <span className="font-mono text-[11px] tabular-nums text-[#1c1410]/45">
                  {String(idx + 1).padStart(2, "0")}
                </span>
                <span className="block h-px flex-1 bg-[#1c1410]/15" />
              </div>
              <h3 className="mt-5 font-editorial text-[26px] font-light leading-tight tracking-tight">
                {moment.label}
              </h3>
              <p className="mt-4 max-w-[32ch] text-[15px] leading-[1.65] text-[#1c1410]/72">
                {moment.body}
              </p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────────────── */

function SoundSection() {
  return (
    <section className="border-b border-[#1c1410]/10">
      <div className="mx-auto grid max-w-[1400px] grid-cols-12 gap-6 px-6 py-24 md:gap-10 md:px-12 md:py-32">
        <div className="col-span-12 lg:col-span-5">
          <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-[#1c1410]/55">
            Der Klang einer Person
          </p>
          <h2 className="mt-4 font-editorial text-[clamp(2rem,4.5vw,3.5rem)] font-light leading-[1.05] tracking-[-0.015em]">
            Eine Stimme hat eine Form.
            <br />
            <span className="italic text-[#b45a3c]">Wir lassen sie sichtbar werden.</span>
          </h2>
          <p className="mt-8 max-w-[42ch] text-[16px] leading-[1.65] text-[#1c1410]/72">
            Aus deiner Tonhöhe, deinen Pausen, deiner Wortwahl entsteht ein
            Vokabular: Farben, Schriften, Spannung, Stille. Die Seite atmet,
            wo du atmest.
          </p>

          <dl className="mt-10 grid grid-cols-2 gap-x-8 gap-y-6">
            {[
              { k: "Tonalität", v: "warm · 0.74" },
              { k: "Rhythmus", v: "ruhig · 0.41" },
              { k: "Klangfarbe", v: "tiefer Mittelton" },
              { k: "Pause-Anteil", v: "23.6 %" },
            ].map((d) => (
              <div key={d.k}>
                <dt className="font-mono text-[10px] uppercase tracking-[0.18em] text-[#1c1410]/50">
                  {d.k}
                </dt>
                <dd className="mt-1 font-editorial text-[20px] tabular-nums">
                  {d.v}
                </dd>
              </div>
            ))}
          </dl>
        </div>

        <figure className="col-span-12 lg:col-span-7">
          <div className="relative aspect-[16/9] w-full overflow-hidden rounded-sm bg-[#f0ebe0]">
            <Image
              src="/landing/voice-abstract.jpg"
              alt="Eine handgemalte, organische Klangwellen-Form in warmem Terrakotta auf Cremefarben."
              fill
              sizes="(min-width: 1024px) 800px, 100vw"
              className="object-cover"
            />
          </div>
          <figcaption className="mt-4 flex items-baseline justify-between font-mono text-[11px] uppercase tracking-[0.18em] text-[#1c1410]/55">
            <span>Yuki · 4.7 Sekunden Lachen</span>
            <span>aus 41 Stunden Material</span>
          </figcaption>
        </figure>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────────────── */

function Modes() {
  return (
    <section id="modi" className="border-b border-[#1c1410]/10 bg-[#1c1410] text-[#faf7f2]">
      <div className="mx-auto max-w-[1400px] px-6 py-24 md:px-12 md:py-32">
        <header className="mb-16 grid grid-cols-12 gap-6 md:mb-20">
          <div className="col-span-12 md:col-span-4">
            <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-[#faf7f2]/45">
              Drei Räume
            </p>
            <h2 className="mt-4 font-editorial text-[clamp(2rem,4.5vw,3.5rem)] font-light leading-[1.05] tracking-[-0.015em]">
              Du betrittst sie,
              <br />
              <span className="italic text-[#d99878]">wann du willst</span>.
            </h2>
          </div>
          <p className="col-span-12 max-w-[48ch] text-[16px] leading-[1.7] text-[#faf7f2]/70 md:col-span-7 md:col-start-6">
            Ein und dieselbe Aufnahme, drei Räume, in denen sie wohnen kann.
            Der Recruiter sieht etwas anderes als der erste Date. Die Tochter
            sieht in zwanzig Jahren etwas Drittes — und alle drei stimmen.
          </p>
        </header>

        <div className="grid grid-cols-12 gap-6 md:gap-10">
          {MODES.map((mode) => (
            <article
              key={mode.badge}
              className="col-span-12 md:col-span-4"
            >
              <BrowserMockup mode={mode} />
              <p className="mt-6 font-mono text-[11px] uppercase tracking-[0.2em] text-[#faf7f2]/50">
                {mode.badge}
              </p>
              <h3 className="mt-2 font-editorial text-[26px] font-light leading-tight tracking-tight">
                {mode.title}
              </h3>
              <p className="mt-3 max-w-[40ch] text-[14.5px] leading-[1.65] text-[#faf7f2]/70">
                {mode.body}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function BrowserMockup({ mode }: { mode: (typeof MODES)[number] }) {
  const [bg, accent, surface] = mode.palette;
  return (
    <div
      className="relative aspect-[4/5] w-full overflow-hidden rounded-md border border-[#faf7f2]/10 shadow-[0_30px_60px_-30px_rgba(0,0,0,0.6)]"
      style={{ background: surface }}
    >
      <div
        className="flex items-center gap-1.5 border-b border-black/10 px-3 py-2"
        style={{ background: surface }}
      >
        <span className="size-2 rounded-full bg-black/15" />
        <span className="size-2 rounded-full bg-black/15" />
        <span className="size-2 rounded-full bg-black/15" />
        <span
          className="ml-2 truncate font-mono text-[9px] tracking-wide"
          style={{ color: bg, opacity: 0.6 }}
        >
          {mode.sample.label.toLowerCase().replace(" · ", "/")}.cw
        </span>
      </div>

      <div className="flex h-full flex-col p-5" style={{ color: bg }}>
        <p
          className="font-mono text-[9px] uppercase tracking-[0.18em]"
          style={{ color: bg, opacity: 0.55 }}
        >
          {mode.sample.label}
        </p>
        <p
          className="mt-3 font-editorial text-[22px] font-light leading-[1.1] tracking-tight"
          style={{ color: bg }}
        >
          Hör mir zu,
          <br />
          <span style={{ color: accent }} className="italic">
            bevor du fragst.
          </span>
        </p>

        <div className="mt-6 space-y-3 border-t border-black/10 pt-4">
          {mode.sample.lines.map((line) => (
            <p
              key={line}
              className="text-[11.5px] leading-snug"
              style={{ color: bg, opacity: 0.75 }}
            >
              {line}
            </p>
          ))}
        </div>

        <div className="mt-auto pt-6">
          <div
            className="flex h-6 items-center gap-1"
            style={{ color: accent }}
          >
            <Waveform className="h-full w-full" bars={64} seed={mode.badge.length * 23} />
          </div>
          <p
            className="mt-2 font-mono text-[9px] tabular-nums"
            style={{ color: bg, opacity: 0.55 }}
          >
            ▸ 02:14 / 04:47
          </p>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────── */

function DeviceSection() {
  return (
    <section className="border-b border-[#1c1410]/10">
      <div className="mx-auto grid max-w-[1400px] grid-cols-12 gap-6 px-6 py-24 md:gap-10 md:px-12 md:py-32">
        <figure className="col-span-12 lg:col-span-6">
          <div className="relative aspect-[4/3] w-full overflow-hidden rounded-sm bg-[#1c1410]/5">
            <Image
              src="/landing/device-stillife.jpg"
              alt="Ein kleines schwarzes Aufnahmegerät an einer Lederkordel, ruht auf einem aufgeschlagenen Notizbuch, daneben eine Tasse Kaffee auf einem Holztisch im warmen Morgenlicht."
              fill
              sizes="(min-width: 1024px) 700px, 100vw"
              className="object-cover"
            />
          </div>
        </figure>

        <div className="col-span-12 flex flex-col justify-center lg:col-span-6 lg:pl-4">
          <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-[#1c1410]/55">
            Was du brauchst
          </p>
          <h2 className="mt-4 font-editorial text-[clamp(2rem,4.5vw,3.5rem)] font-light leading-[1.05] tracking-[-0.015em]">
            Ein Anhänger.
            <br />
            <span className="italic text-[#b45a3c]">Eine Woche.</span>
            <br />
            Sonst nichts.
          </h2>
          <p className="mt-8 max-w-[42ch] text-[16px] leading-[1.7] text-[#1c1410]/72">
            Ein kleiner Recorder, ungefähr so groß wie ein Schlüssel. Du
            trägst ihn nicht ständig — nur dann, wenn du ohnehin gesprochen
            hättest. Sieben Tage reichen für eine erste Form. Danach kannst du
            ihn wegpacken oder weiterhören lassen.
          </p>

          <ul className="mt-10 space-y-3 border-t border-[#1c1410]/10 pt-6">
            {[
              "Du entscheidest, was bleibt — und was gelöscht wird.",
              "Aufnahmen werden verschlüsselt gespeichert. Niemand außer dir hört zu.",
              "Du kannst deine Seite jederzeit komplett zurücknehmen.",
            ].map((line) => (
              <li
                key={line}
                className="flex items-start gap-3 text-[14.5px] leading-[1.6] text-[#1c1410]/80"
              >
                <span className="mt-2 size-1 shrink-0 rounded-full bg-[#b45a3c]" />
                {line}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────────────── */

function FinalCTA() {
  return (
    <section className="bg-[#faf7f2]">
      <div className="mx-auto max-w-[1400px] px-6 py-28 md:px-12 md:py-40">
        <div className="grid grid-cols-12 gap-6 md:gap-10">
          <div className="col-span-12 lg:col-span-8">
            <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-[#1c1410]/55">
              Anfangen
            </p>
            <h2 className="mt-4 font-editorial text-[clamp(2.75rem,7.5vw,6.5rem)] font-light leading-[0.95] tracking-[-0.025em]">
              Sag etwas
              <br />
              <span className="italic text-[#b45a3c]">Wahres.</span>
              <br />
              Den Rest übernehmen wir.
            </h2>
          </div>
          <div className="col-span-12 flex flex-col justify-end lg:col-span-4">
            <p className="max-w-[36ch] text-[16px] leading-[1.7] text-[#1c1410]/72">
              Eine erste Aufnahme, ein erster Entwurf — kostenlos, in unter
              zehn Minuten. Du musst nichts wissen. Nur sprechen.
            </p>
            <div className="mt-10 flex flex-col gap-3">
              <Link
                href="/auth/register"
                className="group inline-flex items-center justify-between rounded-full bg-[#1c1410] px-6 py-4 text-[14px] font-medium text-[#faf7f2] transition hover:bg-[#3a2a20] active:translate-y-[1px]"
              >
                Erste Aufnahme beginnen
                <span className="font-mono text-[11px] tracking-wide text-[#faf7f2]/70 transition group-hover:translate-x-0.5">
                  →
                </span>
              </Link>
              <Link
                href="/auth/login"
                className="text-center text-[13px] text-[#1c1410]/60 underline-offset-4 transition hover:text-[#1c1410] hover:underline"
              >
                Schon angefangen? Hier weitermachen
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─────────────────────────────────────────────────────────────────────────── */

function Footer() {
  return (
    <footer className="border-t border-[#1c1410]/10">
      <div className="mx-auto flex max-w-[1400px] flex-col gap-4 px-6 py-10 md:flex-row md:items-center md:justify-between md:px-12">
        <div className="flex items-center gap-3">
          <span className="font-editorial text-[15px] tracking-tight">
            Character Works
          </span>
          <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-[#1c1410]/50">
            ein Versuch von Cittasana — Berlin
          </span>
        </div>
        <div className="flex items-center gap-6 font-mono text-[11px] uppercase tracking-[0.18em] text-[#1c1410]/55">
          <Link href="#" className="hover:text-[#1c1410]">
            Datenschutz
          </Link>
          <Link href="#" className="hover:text-[#1c1410]">
            Impressum
          </Link>
          <Link
            href="mailto:hallo@cittasana.de"
            className="hover:text-[#1c1410]"
          >
            hallo@cittasana.de
          </Link>
        </div>
      </div>
    </footer>
  );
}
