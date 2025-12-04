import { useEffect, useState } from 'react';
import { checkHealth } from '../../shared/api/health';
import { GlassCard } from '../../components/ui/GlassCard';

export const HomePage = () => {
    const [status, setStatus] = useState<'loading' | 'online' | 'offline'>('loading');
    const [version, setVersion] = useState<string>('');

    useEffect(() => {
        const fetchHealth = async () => {
            try {
                const data = await checkHealth();
                if (data.status === 'ok') {
                    setStatus('online');
                    setVersion(data.version);
                } else {
                    setStatus('offline');
                }
            } catch (error) {
                setStatus('offline');
            }
        };

        fetchHealth();
        // Poll every 10 seconds
        const interval = setInterval(fetchHealth, 10000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="flex flex-col items-center justify-center w-full max-w-2xl mt-20">
            <h1 className="text-6xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent text-center">
                Math Visualizer System
            </h1>

            <GlassCard className="w-full max-w-md">
                <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 text-white">
                    System Status
                </h2>

                <div className="flex items-center justify-between p-4 bg-black/20 rounded-lg border border-white/5">
                    <span className="text-gray-400">Backend API</span>
                    <div className="flex items-center gap-2">
                        {status === 'loading' && (
                            <span className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse" />
                        )}
                        {status === 'online' && (
                            <span className="w-3 h-3 bg-green-500 rounded-full shadow-[0_0_10px_rgba(34,197,94,0.5)]" />
                        )}
                        {status === 'offline' && (
                            <span className="w-3 h-3 bg-red-500 rounded-full" />
                        )}
                        <span className="uppercase text-sm font-bold tracking-wider text-white">
                            {status}
                        </span>
                    </div>
                </div>

                {version && (
                    <div className="mt-4 text-xs text-gray-500 text-center">
                        v{version}
                    </div>
                )}
            </GlassCard>

            <div className="mt-12 text-center max-w-lg">
                <p className="text-white/60 text-lg">
                    Welcome to the Next-Gen Math Visualization Platform.
                    Navigate to the <strong>Visualizer</strong> to start exploring.
                </p>
            </div>
        </div>
    );
};
