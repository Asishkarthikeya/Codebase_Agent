'use client';

import { motion } from 'framer-motion';
import { useState } from 'react';
import { Sparkles, FileCode, Save, MessageSquare } from 'lucide-react';

export default function GeneratePage() {
    const [featureDesc, setFeatureDesc] = useState('');
    const [framework, setFramework] = useState('Auto-detect');
    const [includeTests, setIncludeTests] = useState(true);
    const [includeDocs, setIncludeDocs] = useState(true);
    const [isGenerating, setIsGenerating] = useState(false);
    const [result, setResult] = useState<string | null>(null);

    const examples = [
        'Create a user authentication system with JWT tokens',
        'Build a REST API endpoint for file uploads',
        'Add a caching layer with Redis',
        'Generate unit tests for the auth module',
    ];

    const handleGenerate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!featureDesc.trim()) return;

        setIsGenerating(true);

        try {
            const response = await fetch('http://localhost:8000/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: `Generate a complete implementation for: ${featureDesc}. Framework: ${framework}. Include tests: ${includeTests}. Include docs: ${includeDocs}.`,
                }),
            });

            const data = await response.json();
            setResult(data.answer || data.response || 'No response received');
        } catch (error) {
            console.error('Generation failed:', error);
            setResult('Error connecting to backend');
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="flex flex-col h-screen">
            {/* Header */}
            <motion.header
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 m-4 mb-0"
            >
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-400 to-fuchsia-500 flex items-center justify-center">
                        ✨
                    </div>
                    <div>
                        <h1 className="font-bold text-lg">Generate Mode</h1>
                        <p className="text-sm text-slate-400">Create complete features from descriptions</p>
                    </div>
                </div>

                {/* Examples */}
                <div className="flex flex-wrap gap-2 mb-4">
                    {examples.map((example) => (
                        <motion.button
                            key={example}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => setFeatureDesc(example)}
                            className="px-3 py-1.5 bg-slate-800 rounded-lg text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                        >
                            {example.slice(0, 40)}...
                        </motion.button>
                    ))}
                </div>

                {/* Form */}
                <form onSubmit={handleGenerate} className="space-y-4">
                    <div>
                        <label className="block text-sm text-slate-400 mb-2">Feature Description</label>
                        <textarea
                            value={featureDesc}
                            onChange={(e) => setFeatureDesc(e.target.value)}
                            placeholder="Describe the feature you want to build in detail..."
                            rows={4}
                            className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl focus:border-violet-500 focus:outline-none transition-colors resize-none"
                        />
                    </div>

                    <div className="flex gap-4">
                        <div className="flex-1">
                            <label className="block text-sm text-slate-400 mb-2">Framework</label>
                            <select
                                value={framework}
                                onChange={(e) => setFramework(e.target.value)}
                                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl focus:border-violet-500 focus:outline-none transition-colors"
                            >
                                <option>Auto-detect</option>
                                <option>FastAPI</option>
                                <option>Flask</option>
                                <option>Django</option>
                                <option>Express.js</option>
                                <option>React</option>
                            </select>
                        </div>

                        <label className="flex items-center gap-2 px-4 py-3 bg-slate-800/50 rounded-xl cursor-pointer">
                            <input
                                type="checkbox"
                                checked={includeTests}
                                onChange={(e) => setIncludeTests(e.target.checked)}
                                className="w-4 h-4 accent-violet-500"
                            />
                            <span className="text-sm text-slate-300">Tests</span>
                        </label>

                        <label className="flex items-center gap-2 px-4 py-3 bg-slate-800/50 rounded-xl cursor-pointer">
                            <input
                                type="checkbox"
                                checked={includeDocs}
                                onChange={(e) => setIncludeDocs(e.target.checked)}
                                className="w-4 h-4 accent-violet-500"
                            />
                            <span className="text-sm text-slate-300">Docs</span>
                        </label>
                    </div>

                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        type="submit"
                        disabled={isGenerating || !featureDesc.trim()}
                        className="w-full py-3 bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-xl font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                        {isGenerating ? (
                            <>
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                Generating...
                            </>
                        ) : (
                            <>
                                <Sparkles className="w-5 h-5" />
                                Generate Feature
                            </>
                        )}
                    </motion.button>
                </form>
            </motion.header>

            {/* Result */}
            <div className="flex-1 overflow-y-auto p-4">
                {result && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-4"
                    >
                        {/* Actions */}
                        <div className="flex gap-2">
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                className="flex items-center gap-2 px-4 py-2 bg-green-500/20 text-green-400 rounded-lg"
                            >
                                <Save className="w-4 h-4" />
                                Save Files
                            </motion.button>
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                className="flex items-center gap-2 px-4 py-2 bg-sky-500/20 text-sky-400 rounded-lg"
                            >
                                <MessageSquare className="w-4 h-4" />
                                Discuss
                            </motion.button>
                        </div>

                        {/* Generated Content */}
                        <div className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6">
                            <div className="flex items-center gap-2 mb-4 pb-4 border-b border-white/10">
                                <FileCode className="w-5 h-5 text-violet-400" />
                                <span className="font-medium">Generated Feature</span>
                            </div>
                            <div className="prose prose-invert max-w-none">
                                <pre className="whitespace-pre-wrap text-sm">{result}</pre>
                            </div>
                        </div>
                    </motion.div>
                )}

                {!result && !isGenerating && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex flex-col items-center justify-center h-64 text-slate-500"
                    >
                        <Sparkles className="w-12 h-12 mb-4 opacity-50" />
                        <p>Describe a feature above to generate code</p>
                    </motion.div>
                )}
            </div>
        </div>
    );
}
