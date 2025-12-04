import { useAnalyzeNumber } from "../../features/analysis/hooks/useAnalyzeNumber";
import { AnalysisForm } from "../../features/analysis/components/AnalysisForm";
import { AnalysisResult } from "../../features/analysis/components/AnalysisResult";
import { GlassCard } from "../../components/ui/GlassCard";

export function AnalysisPage() {
    const { result, loading, error, analyze } = useAnalyzeNumber();

    return (
        <div className="w-full max-w-2xl mx-auto">
            <header className="text-center mb-12">
                <h1 className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 mb-4">
                    Math Visualizer
                </h1>
                <p className="text-white/60 text-lg">
                    Explore the beauty of numbers through neural glass.
                </p>
            </header>

            <AnalysisForm onAnalyze={analyze} loading={loading} />

            {error && (
                <GlassCard className="mt-8 border-red-500/30 bg-red-500/10">
                    <p className="text-red-200 text-center">{error}</p>
                </GlassCard>
            )}

            {result && <AnalysisResult result={result} />}
        </div>
    );
}
