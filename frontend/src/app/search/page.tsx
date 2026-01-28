'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { Search, FileCode, ChevronDown, ChevronRight } from 'lucide-react';

interface SearchResult {
    file_path: string;
    line_number: number;
    line_content: string;
    context_before: string[];
    context_after: string[];
}

export default function SearchPage() {
    const [pattern, setPattern] = useState('');
    const [filePattern, setFilePattern] = useState('**/*.py');
    const [results, setResults] = useState<SearchResult[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [expandedResults, setExpandedResults] = useState<Set<number>>(new Set());

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!pattern.trim()) return;

        setIsSearching(true);

        try {
            const response = await fetch('http://localhost:8000/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    pattern,
                    file_pattern: filePattern,
                    context_lines: 2
                }),
            });

            const data = await response.json();
            setResults(data.results || []);
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            setIsSearching(false);
        }
    };

    const toggleExpand = (index: number) => {
        const newExpanded = new Set(expandedResults);
        if (newExpanded.has(index)) {
            newExpanded.delete(index);
        } else {
            newExpanded.add(index);
        }
        setExpandedResults(newExpanded);
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
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center">
                        🔍
                    </div>
                    <div>
                        <h1 className="font-bold text-lg">Search Mode</h1>
                        <p className="text-sm text-slate-400">Find patterns across your codebase</p>
                    </div>
                </div>

                {/* Search Form */}
                <form onSubmit={handleSearch} className="space-y-4">
                    <div className="flex gap-4">
                        <div className="flex-1">
                            <label className="block text-sm text-slate-400 mb-2">Search Pattern (regex)</label>
                            <input
                                type="text"
                                value={pattern}
                                onChange={(e) => setPattern(e.target.value)}
                                placeholder="e.g., class\s+(\w+) or def.*login"
                                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl focus:border-sky-500 focus:outline-none transition-colors"
                            />
                        </div>
                        <div className="w-48">
                            <label className="block text-sm text-slate-400 mb-2">File Pattern</label>
                            <input
                                type="text"
                                value={filePattern}
                                onChange={(e) => setFilePattern(e.target.value)}
                                placeholder="**/*.py"
                                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl focus:border-sky-500 focus:outline-none transition-colors"
                            />
                        </div>
                    </div>

                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        type="submit"
                        disabled={isSearching || !pattern.trim()}
                        className="w-full py-3 bg-gradient-to-r from-emerald-500 to-cyan-500 rounded-xl font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                        {isSearching ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <>
                                <Search className="w-5 h-5" />
                                Search Codebase
                            </>
                        )}
                    </motion.button>
                </form>
            </motion.header>

            {/* Results */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {results.length > 0 && (
                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-sm text-slate-400 mb-4"
                    >
                        Found {results.length} matches
                    </motion.p>
                )}

                <AnimatePresence>
                    {results.map((result, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.03 }}
                            className="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-2xl p-6 !p-0 overflow-hidden"
                        >
                            {/* Header */}
                            <button
                                onClick={() => toggleExpand(i)}
                                className="w-full flex items-center gap-3 p-4 hover:bg-white/5 transition-colors"
                            >
                                {expandedResults.has(i) ? (
                                    <ChevronDown className="w-4 h-4 text-slate-400" />
                                ) : (
                                    <ChevronRight className="w-4 h-4 text-slate-400" />
                                )}
                                <FileCode className="w-4 h-4 text-sky-400" />
                                <span className="text-sm font-medium text-slate-300">
                                    {result.file_path}
                                </span>
                                <span className="text-xs text-slate-500">
                                    Line {result.line_number}
                                </span>
                            </button>

                            {/* Code Preview */}
                            <AnimatePresence>
                                {expandedResults.has(i) && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        className="border-t border-slate-700"
                                    >
                                        <pre className="p-4 text-sm overflow-x-auto !rounded-none !border-0">
                                            {result.context_before?.map((line, j) => (
                                                <div key={`before-${j}`} className="text-slate-500">{line}</div>
                                            ))}
                                            <div className="bg-sky-500/20 text-sky-200 -mx-4 px-4 py-1 border-l-2 border-sky-400">
                                                {result.line_content}
                                            </div>
                                            {result.context_after?.map((line, j) => (
                                                <div key={`after-${j}`} className="text-slate-500">{line}</div>
                                            ))}
                                        </pre>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {results.length === 0 && !isSearching && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex flex-col items-center justify-center h-64 text-slate-500"
                    >
                        <Search className="w-12 h-12 mb-4 opacity-50" />
                        <p>Enter a pattern to search your codebase</p>
                    </motion.div>
                )}
            </div>
        </div>
    );
}
