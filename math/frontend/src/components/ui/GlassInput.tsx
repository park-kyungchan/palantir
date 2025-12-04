import { motion, type HTMLMotionProps } from "framer-motion";
import { cn } from "../../lib/utils";

interface GlassInputProps extends HTMLMotionProps<"input"> { }

export function GlassInput({ className, ...props }: GlassInputProps) {
    return (
        <motion.input
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={cn(
                "w-full bg-black/20 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/30",
                "focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent",
                "backdrop-blur-sm transition-all duration-200",
                className
            )}
            {...props}
        />
    );
}
