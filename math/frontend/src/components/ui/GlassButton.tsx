import { motion, type HTMLMotionProps } from "framer-motion";
import { cn } from "../../lib/utils";

interface GlassButtonProps extends HTMLMotionProps<"button"> {
    variant?: "primary" | "secondary";
}

export function GlassButton({ children, className, variant = "primary", ...props }: GlassButtonProps) {
    const variants = {
        primary: "bg-blue-600/80 hover:bg-blue-500/90 text-white border-blue-400/30",
        secondary: "bg-white/5 hover:bg-white/10 text-white border-white/10",
    };

    return (
        <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className={cn(
                "px-6 py-3 rounded-xl font-medium backdrop-blur-sm border transition-all duration-200",
                "flex items-center justify-center gap-2 shadow-lg",
                variants[variant],
                className
            )}
            {...props}
        >
            {children}
        </motion.button>
    );
}
