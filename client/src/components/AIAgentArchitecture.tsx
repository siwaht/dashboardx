import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Brain, Database, MessageSquare, Search, Zap, Globe, Server, FileText } from "lucide-react";

export default function AIAgentArchitecture() {
    const containerRef = useRef<HTMLDivElement>(null);

    return (
        <div ref={containerRef} className="w-full h-full min-h-[400px] flex items-center justify-center p-4 bg-gradient-to-br from-background/50 to-primary/5 backdrop-blur-sm rounded-xl border border-white/10 overflow-hidden relative">
            <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:20px_20px]" />

            {/* Main Architecture Flow */}
            <div className="relative z-10 flex flex-col md:flex-row items-center gap-8 md:gap-12 max-w-4xl w-full">

                {/* Input Source */}
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5 }}
                    className="flex flex-col items-center gap-2"
                >
                    <div className="p-4 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md shadow-xl">
                        <Globe className="w-8 h-8 text-blue-400" />
                    </div>
                    <span className="text-xs font-medium text-muted-foreground">Data Sources</span>
                </motion.div>

                {/* Connection Line 1 */}
                <div className="h-12 w-[2px] md:h-[2px] md:w-12 bg-gradient-to-b md:bg-gradient-to-r from-blue-500/50 to-purple-500/50 relative overflow-hidden">
                    <motion.div
                        className="absolute inset-0 bg-white shadow-[0_0_10px_rgba(255,255,255,0.5)]"
                        initial={{ x: "-100%", opacity: 0 }}
                        animate={{ x: "100%", opacity: [0, 1, 0] }}
                        transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                    />
                </div>

                {/* Processing Core */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                    className="relative"
                >
                    <div className="absolute -inset-4 bg-gradient-to-r from-purple-500/20 to-blue-500/20 blur-xl rounded-full animate-pulse" />
                    <div className="p-6 rounded-3xl bg-black/40 border border-white/10 backdrop-blur-xl shadow-2xl relative overflow-hidden group">
                        <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        <Brain className="w-12 h-12 text-purple-400" />

                        {/* Orbiting Elements */}
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ repeat: Infinity, duration: 10, ease: "linear" }}
                            className="absolute inset-0"
                        >
                            <div className="absolute top-2 left-1/2 -translate-x-1/2 w-2 h-2 bg-blue-400 rounded-full blur-[1px]" />
                        </motion.div>
                    </div>
                    <span className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs font-medium text-muted-foreground whitespace-nowrap">AI Core</span>
                </motion.div>

                {/* Connection Line 2 */}
                <div className="h-12 w-[2px] md:h-[2px] md:w-12 bg-gradient-to-b md:bg-gradient-to-r from-purple-500/50 to-green-500/50 relative overflow-hidden">
                    <motion.div
                        className="absolute inset-0 bg-white shadow-[0_0_10px_rgba(255,255,255,0.5)]"
                        initial={{ x: "-100%", opacity: 0 }}
                        animate={{ x: "100%", opacity: [0, 1, 0] }}
                        transition={{ repeat: Infinity, duration: 2, delay: 1, ease: "linear" }}
                    />
                </div>

                {/* Output Actions */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5, delay: 0.4 }}
                    className="grid grid-cols-2 gap-3"
                >
                    {[
                        { icon: MessageSquare, color: "text-green-400", label: "Chat" },
                        { icon: FileText, color: "text-yellow-400", label: "Report" },
                        { icon: Database, color: "text-red-400", label: "Store" },
                        { icon: Zap, color: "text-orange-400", label: "Action" }
                    ].map((item, i) => (
                        <motion.div
                            key={i}
                            whileHover={{ scale: 1.05, backgroundColor: "rgba(255,255,255,0.1)" }}
                            className="p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur-md flex flex-col items-center gap-2 cursor-pointer transition-colors"
                        >
                            <item.icon className={`w-5 h-5 ${item.color}`} />
                            <span className="text-[10px] font-medium text-muted-foreground">{item.label}</span>
                        </motion.div>
                    ))}
                </motion.div>
            </div>

            {/* Floating Particles */}
            {[...Array(5)].map((_, i) => (
                <motion.div
                    key={i}
                    className="absolute w-1 h-1 bg-white/30 rounded-full"
                    initial={{
                        x: Math.random() * 400 - 200,
                        y: Math.random() * 400 - 200,
                        opacity: 0
                    }}
                    animate={{
                        y: [0, -20, 0],
                        opacity: [0, 0.5, 0],
                        scale: [0, 1.5, 0]
                    }}
                    transition={{
                        repeat: Infinity,
                        duration: 3 + Math.random() * 2,
                        delay: Math.random() * 2,
                        ease: "easeInOut"
                    }}
                />
            ))}
        </div>
    );
}
