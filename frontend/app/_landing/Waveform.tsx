type Props = {
  className?: string
  bars?: number
  seed?: number
}

function deterministicHeights(count: number, seed: number) {
  const heights: number[] = []
  let x = seed
  for (let i = 0; i < count; i++) {
    x = (x * 9301 + 49297) % 233280
    const v = (x / 233280) * 0.85 + 0.15
    const taper = Math.sin((i / count) * Math.PI)
    heights.push(v * taper)
  }
  return heights
}

export function Waveform({ className, bars = 96, seed = 17 }: Props) {
  const heights = deterministicHeights(bars, seed)
  const gap = 0.4
  const barW = 1
  const stride = barW + gap

  return (
    <svg
      viewBox={`0 0 ${stride * bars} 24`}
      preserveAspectRatio="none"
      aria-hidden
      className={className}
    >
      {heights.map((h, i) => {
        const height = Math.max(0.6, h * 22)
        const y = (24 - height) / 2
        return (
          <rect
            key={i}
            x={i * stride}
            y={y}
            width={barW}
            height={height}
            rx={0.4}
            fill="currentColor"
          />
        )
      })}
    </svg>
  )
}
