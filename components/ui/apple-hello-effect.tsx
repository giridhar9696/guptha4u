import { motion } from "framer-motion"
import type { ReactNode } from "react"

// The supplied Apple Hello effect draws each SVG stroke using Motion's pathLength.
export function KalamWritingEffect({ strokes, reduced, onComplete }: {
  strokes: string[]
  reduced: boolean
  onComplete: () => void
}): ReactNode {
  return <motion.svg className="kalam-signature" viewBox="0 0 350 120" fill="none" stroke="currentColor"
    strokeWidth="5.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"
    initial={{ opacity: 1 }} animate={{ opacity: [1, 1, 0] }}
    transition={{ duration: reduced ? .16 : 1.85, times: [0, .87, 1] }} onAnimationComplete={onComplete}>
    {strokes.map((d, index) => <motion.path key={d} d={d}
      initial={reduced ? false : { pathLength: 0, opacity: 0 }}
      animate={{ pathLength: 1, opacity: 1 }}
      transition={reduced ? { duration: 0 } : {
        pathLength: { duration: index ? 1.36 : .23, delay: index ? .19 : 0, ease: index ? "linear" : "easeInOut" },
        opacity: { duration: .08, delay: index ? .19 : 0 },
      }} />)}
  </motion.svg>
}
