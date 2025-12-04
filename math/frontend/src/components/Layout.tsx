import { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "../lib/utils";

interface LayoutProps {
    children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
    const location = useLocation();

    const navItems = [
        { name: "Home", path: "/" },
        { name: "Visualizer", path: "/analyze" },
    ];

    return (
        <div className="min-h-screen bg-slate-950 text-white flex flex-col relative overflow-hidden">
            {/* Background Gradients */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
                <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-600/20 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-600/20 rounded-full blur-[120px]" />
            </div>

            {/* Navigation */}
            <nav className="relative z-50 p-6 flex justify-center">
                <div className="flex gap-4 bg-white/5 backdrop-blur-md border border-white/10 rounded-full px-6 py-2 shadow-xl">
                    {navItems.map((item) => (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={cn(
                                "px-4 py-2 rounded-full text-sm font-medium transition-all duration-300",
                                location.pathname === item.path
                                    ? "bg-white/10 text-white shadow-inner"
                                    : "text-white/60 hover:text-white hover:bg-white/5"
                            )}
                        >
                            {item.name}
                        </Link>
                    ))}
                </div>
            </nav>

            {/* Content */}
            <main className="relative z-10 flex-1 p-4 flex flex-col items-center w-full">
                {children}
            </main>
        </div>
    );
}
