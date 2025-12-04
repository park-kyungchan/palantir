import { useState } from "react";
import { motion } from "framer-motion";
import { Zap } from "lucide-react";

interface NumberInputProps {
    onSubmit: (num: number) => void;
    isLoading: boolean;
}

export function NumberInput({ onSubmit, isLoading }: NumberInputProps) {
    const [value, setValue] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const num = parseInt(value);
        if (!isNaN(num)) {
            onSubmit(num);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="relative">
                <input
                    type="number"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    placeholder="Enter a number..."
                    className="w-full px-6 py-4 bg-black/20 border border-white/10 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-lg"
                    disabled={isLoading}
                />
            </div>
            <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={!value || isLoading}
                className="w-full py-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl font-bold text-lg shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
                {isLoading ? (
                    <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                    <>
                        <Zap className="w-5 h-5" />
                        <span>Analyze Number</span>
                    </>
                )}
            </motion.button>
        </form>
    );
}
