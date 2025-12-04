import { motion } from "framer-motion";
import type { ReactNode } from "react";

interface GlassCardProps {
    children: ReactNode;
    className?: string;
}

export const GlassCard = ({ children, className = "" }: GlassCardProps) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className={`backdrop-blur-md bg-white/10 border border-white/20 rounded-2xl shadow-xl p-6 ${className}`}
        >
            {children}
        </motion.div>
    );
};
