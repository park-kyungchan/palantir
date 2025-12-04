import { motion } from "framer-motion";
import { cn } from "../../lib/utils";
import { type ReactNode } from "react";

interface GlassCardProps {
    children: ReactNode;
    className?: string;
}

export function GlassCard({ children, className }: GlassCardProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className={cn(
                "backdrop-blur-md bg-white/5 border border-white/10 shadow-2xl rounded-2xl p-6",
                "hover:bg-white/10 transition-colors duration-300",
                className
            )}
        >
            {children}
        </motion.div>
    );
}
