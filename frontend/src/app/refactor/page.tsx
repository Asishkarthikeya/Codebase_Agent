'use client';

import { motion } from 'framer-motion';
import { useState } from 'react';
import { Wrench, Play, Eye, CheckCircle, XCircle } from 'lucide-react';

export default function RefactorPage() {
    const [searchPattern, setSearchPattern] = useState('');
    const [replacePattern, setReplacePattern] = useState('');
    const [filePattern, setFilePattern] = useState('**/*.py');
    const [isDryRun, setIsDryRun] = useState(true);
    const [isRefactoring, setIsRefactoring] = useState(false);
    const [result, setResult] = useState<any>(null);

    const commonPatterns = [
        { name: 'print → logging', search: 'print\\((.*)\\)', replace: 'logger.info(\\1)' },
        { name: 'assertEqual → assert', search: 'assertEqual\\(([^,]+),\\s*([^)]+)\\)', replace: 'assert \\1 == \\2' },
        { name: 'Remove trailing whitespace', search: '[ \\t]+$', replace: '' },
    ];

    const handleRefactor = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!searchPattern.trim() || !replacePattern) return;

        setIsRefactoring(true);

        try {
            const response = await fetch('http://localhost:8000/api/refactor', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    search_pattern: searchPattern,
                    replace_pattern: replacePattern,
                    file_pattern: filePattern,
                    dry_run: isDryRun,
                }),
            });

            const data = await response.json();
            setResult(data);
        } catch (error) {
            console.error('Refactor failed:', error);
        } finally {
            setIsRefactoring(false);
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
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center">
                        🔧
                    </div>
                    <div>
                        <h1 className="font-bold text-lg">Refactor Mode</h1>
                        <p className="text-sm text-slate-400">Automated code refactoring with regex</p>
                    </div>
                </div>

                {/* Common Patterns */}
                <div className="flex gap-2 mb-4">
                    {commonPatterns.map((p) => (
                        <motion.button
                            key={p.name}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => {
                                setSearchPattern(p.search);
                                setReplacePattern(p.replace);
                            }}
                            className="px-3 py-1.5 bg-slate-800 rounded-lg text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                        >
                            {p.name}
                        </motion.button>
                    ))}
                </div>

                {/* Form */}
                <form onSubmit={handleRefactor} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-slate-400 mb-2">Search Pattern</label>
                            <input
                                type="text"
                                value={searchPattern}
                                onChange={(e) => setSearchPattern(e.target.value)}
                                placeholder="e.g., print\((.*)\)"
                                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl focus:border-orange-500 focus:outline-none transition-colors font-mono text-sm"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-slate-400 mb-2">Replace Pattern</label>
                            <input
                                type="text"
                                value={replacePattern}
                                onChange={(e) => setReplacePattern(e.target.value)}
                                placeholder="e.g., logger.info(\1)"
                                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl focus:border-orange-500 focus:outline-none transition-colors font-mono text-sm"
                            />
                        </div>
                    </div>

                    <div className="flex gap-4 items-end">
                        <div className="flex-1">
                            <label className="block text-sm text-slate-400 mb-2">File Pattern</label>
                            <input
                                type="text"
                                value={filePattern}
                                onChange={(e) => setFilePattern(e.target.value)}
                                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl focus:border-orange-500 focus:outline-none transition-colors"
                            />
                        </div>

                        <label className="flex items-center gap-2 px-4 py-3 bg-slate-800/50 rounded-xl cursor-pointer">
                            <input
                                type="checkbox"
                                checked={isDryRun}
                                onChange={(e) => setIsDryRun(e.target.checked)}
                                className="w-4 h-4 accent-orange-500"
                            />
                            <span className="text-sm text-slate-300">Dry Run</span>
                            <Eye className="w-4 h-4 text-slate-400" />
                        </label>
                    </div>

                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        type="submit"
                        disabled={isRefactoring || !searchPattern.trim()}
                        className="w-full py-3 bg-gradient-to-r from-orange-500 to-red-500 rounded-xl font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                        {isRefactoring ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <>
                                <Wrench className="w-5 h-5" />
                                {isDryRun ? 'Preview Changes' : 'Apply Refactoring'}
                            </>
                        )}
                    </motion.button>
                </form>
            </motion.header>

            {/* Results */}
            <div className="flex-1 overflow-y-auto p-4">
                {result && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-4"
                    >
                        {/* Summary */}
                        <div className={`bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 flex items-center gap-4 ${result.success ? 'border-green-500/30' : 'border-red-500/30'
                            }`}>
                            {result.success ? (
                                <CheckCircle className="w-8 h-8 text-green-400" />
                            ) : (
                                <XCircle className="w-8 h-8 text-red-400" />
                            )}
                            <div>
                                <p className="font-semibold">
                                    {result.success
                                        ? `${isDryRun ? 'Preview:' : 'Applied:'} ${result.files_changed || 0} files, ${result.total_replacements || 0} replacements`
                                        : 'Refactoring failed'
                                    }
                                </p>
                                {result.error && (
                                    <p className="text-sm text-red-400">{result.error}</p>
                                )}
                            </div>
                        </div>

                        {/* Changes */}
                        {result.changes?.map((change: any, i: number) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: i * 0.05 }}
                                className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6"
                            >
                                <p className="text-sm font-medium text-slate-300 mb-2">
                                    📄 {change.file_path} ({change.replacements} changes)
                                </p>
                                {change.preview && (
                                    <pre className="text-xs overflow-x-auto">{change.preview}</pre>
                                )}
                            </motion.div>
                        ))}
                    </motion.div>
                )}

                {!result && !isRefactoring && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex flex-col items-center justify-center h-64 text-slate-500"
                    >
                        <Wrench className="w-12 h-12 mb-4 opacity-50" />
                        <p>Configure patterns above to preview or apply refactoring</p>
                    </motion.div>
                )}
            </div>
        </div>
    );
}
