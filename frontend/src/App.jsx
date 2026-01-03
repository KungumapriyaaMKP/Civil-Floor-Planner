import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import html2canvas from 'html2canvas';
import {
  Plus,
  Trash2,
  Layout,
  Box as BoxIcon,
  Mic,
  MicOff,
  ChevronRight,
  Activity,
  Maximize2,
  Layers,
  Settings,
  Download,
  Share2,
  Menu,
  X,
  Compass,
  AudioLines,
  Sparkles
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = window.location.hostname === "localhost"
  ? "http://localhost:7860/api"
  : "https://kungumapriyaa-civil-project.hf.space/api";

const App = () => {
  const [plotSize, setPlotSize] = useState("40x30");
  const [roomText, setRoomText] = useState("Master Bedroom, 14, 12, top-left\nLiving, 20, 15, center\nKitchen, 12, 10, bottom-right\nBath, 8, 6, any");
  const [layout, setLayout] = useState(null);
  const [plotlyData, setPlotlyData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [error, setError] = useState(null);

  const blueprintRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Auto-generate on load if data exists
  useEffect(() => {
    if (roomText && !layout) generateLayout();
  }, []);

  const generateLayout = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await axios.post(`${API_BASE}/generate`, {
        plot_size: plotSize,
        room_text: roomText
      });
      setLayout(resp.data);
      setPlotlyData(null);
    } catch (err) {
      console.error(err);
      setError(`API Error: ${err.message}. Check if Backend is Running.`);
    } finally {
      setLoading(false);
    }
  };

  const generate3D = async () => {
    if (!layout) return;
    setLoading(true);
    try {
      const resp = await axios.post(`${API_BASE}/visualize`, {
        plot: layout.plot,
        rooms: layout.rooms,
        placed: layout.placed
      });
      setPlotlyData(resp.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const exportPX = async () => {
    if (blueprintRef.current) {
      const canvas = await html2canvas(blueprintRef.current, {
        backgroundColor: '#0a0a0c',
        scale: 2,
        useCORS: true
      });
      const link = document.createElement('a');
      link.download = `CivilFloorPlan_${plotSize}.png`;
      link.href = canvas.toDataURL("image/png");
      link.click();
    }
  };

  const shareProject = () => {
    navigator.clipboard.writeText(window.location.href);
    alert("Project workspace link copied to clipboard!");
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      mediaRecorderRef.current.ondataavailable = (e) => audioChunksRef.current.push(e.data);
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'voice.wav');
        const resp = await axios.post(`${API_BASE}/transcribe`, formData);
        setRoomText(prev => prev + "\n" + resp.data.parsed);
      };
      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) { alert("Microphone access denied"); }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      mediaRecorderRef.current.stream.getTracks().forEach(t => t.stop());
    }
  };

  return (
    <div className="fixed inset-0 bg-[#0a0a0c] text-slate-200 font-sans selection:bg-indigo-500/30 overflow-hidden flex">
      {/* Sidebar Overlay for Mobile */}
      <AnimatePresence>
        {!sidebarOpen && (
          <motion.button
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            onClick={() => setSidebarOpen(true)}
            className="absolute top-6 left-6 z-50 p-3 bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl hover:bg-zinc-800 transition-colors"
          >
            <Menu className="w-5 h-5 text-indigo-400" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ width: sidebarOpen ? 400 : 0, opacity: sidebarOpen ? 1 : 0 }}
        className="relative h-full bg-[#0f0f12] border-r border-zinc-800 shadow-2xl flex flex-col z-40 overflow-hidden"
      >
        <div className="p-8 flex items-center justify-between border-b border-zinc-900/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20 shrink-0">
              <Compass className="text-white w-6 h-6" />
            </div>
            <div>
              <h1 className="text-base font-black tracking-tight text-white leading-tight uppercase">CIVIL FLOOR PLAN <br /><span className="text-indigo-500">GENERATOR</span></h1>
              <p className="text-[9px] text-zinc-500 font-bold uppercase tracking-[0.2em] mt-1">Industrial Intelligence</p>
            </div>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="p-2 hover:bg-zinc-800 rounded-lg transition-colors shrink-0">
            <X className="w-4 h-4 text-zinc-500" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-8">
          {/* Explicit Voice Assistant Panel */}
          <section className="bg-gradient-to-br from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 p-5 rounded-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="bg-indigo-500/20 p-2 rounded-lg">
                <Mic className="w-4 h-4 text-indigo-400" />
              </div>
              <div>
                <h3 className="text-xs font-black text-white uppercase tracking-wider">Voice Control</h3>
                <p className="text-[10px] text-zinc-500 font-medium">Dictate your floor plan</p>
              </div>
            </div>

            <button
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              className={`w-full py-4 rounded-xl flex items-center justify-center gap-3 font-bold text-xs tracking-widest transition-all ${isRecording
                ? "bg-red-500 text-white shadow-[0_0_20px_rgba(239,68,68,0.4)] animate-pulse"
                : "bg-zinc-900 border border-zinc-800 text-slate-300 hover:border-indigo-500/50 hover:text-white group"
                }`}
            >
              {isRecording ? (
                <>
                  <AudioLines className="w-4 h-4 animate-bounce" />
                  LISTENING...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-indigo-500 group-hover:scale-125 transition-transform" />
                  HOLD TO COMMAND
                </>
              )}
            </button>
            <p className="text-[9px] text-zinc-600 text-center font-medium italic">Try: "Add a bedroom 15 by 12 top right"</p>
          </section>

          {/* Plot Size */}
          <section className="space-y-3">
            <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              <Maximize2 className="w-3.5 h-3.5" /> Site Plot Size
            </label>
            <input
              value={plotSize}
              onChange={(e) => setPlotSize(e.target.value)}
              className="w-full bg-zinc-900/50 border border-zinc-800 p-4 rounded-xl text-white font-mono focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/50 outline-none transition-all placeholder:text-zinc-700"
              placeholder="e.g. 50x40"
            />
          </section>

          {/* Room Spec */}
          <section className="space-y-3">
            <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              <Layers className="w-3.5 h-3.5" /> Manual Specifications
            </label>
            <div className="relative group">
              <textarea
                value={roomText}
                onChange={(e) => setRoomText(e.target.value)}
                className="w-full h-48 bg-zinc-900/50 border border-zinc-800 p-5 rounded-2xl text-zinc-300 text-xs font-mono leading-relaxed focus:ring-2 focus:ring-indigo-500/20 outline-none transition-all resize-none group-hover:border-zinc-700 shadow-inner"
                placeholder="Room Name, Width, Depth, Position..."
              />
              <div className="absolute bottom-4 right-4 text-[9px] text-zinc-600 font-medium select-none pointer-events-none tracking-tight">
                NAME, W, D, POS
              </div>
            </div>
          </section>

          <button
            onClick={generateLayout}
            disabled={loading}
            className="w-full group relative overflow-hidden bg-white text-black py-5 rounded-2xl font-black text-xs tracking-[0.15em] hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 mt-4 shadow-xl"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-500 opacity-0 group-hover:opacity-10 transition-opacity" />
            <div className="flex items-center justify-center gap-3">
              {loading ? <Activity className="w-5 h-5 animate-spin" /> : <Layout className="w-5 h-5 group-hover:rotate-6 transition-transform" />}
              COMPUTE BLUEPRINT
              <ChevronRight className="w-4 h-4 text-zinc-400 group-hover:translate-x-1 transition-transform" />
            </div>
          </button>
        </div>

        <div className="p-8 border-t border-zinc-900/50 bg-black/20 text-center space-y-3">
          {error && (
            <p className="text-[10px] text-red-500 font-bold bg-red-500/10 p-2 rounded-lg border border-red-500/20 italic">
              {error}
            </p>
          )}
          <p className="text-[9px] text-zinc-600 font-bold tracking-widest flex items-center justify-center gap-2">
            <Settings className="w-3 h-3" /> ENGINE READY [v1.0.6-final]
          </p>
        </div>
      </motion.aside>

      {/* Main Content Viewport */}
      <main className="flex-1 relative overflow-y-auto overflow-x-hidden custom-scrollbar bg-[#0a0a0c] selection:bg-indigo-500/20 p-8 pt-20 lg:p-12">
        <div className="max-w-6xl mx-auto space-y-12 pb-24">

          {/* Header Area */}
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 px-4">
            <div className="space-y-2">
              <h2 className="text-3xl font-black text-white tracking-tight flex items-center gap-4">
                Active Canvas <span className="text-zinc-800 text-lg">/</span> <span className="text-indigo-500 text-xl font-mono tracking-widest">{plotSize}FT</span>
              </h2>
              <p className="text-zinc-500 text-sm font-medium">Automated Layout Synthesis Engine</p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={exportPX}
                className="flex items-center gap-2 px-5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-xl text-[10px] font-black text-zinc-300 hover:text-white transition-all uppercase tracking-widest"
              >
                <Download className="w-4 h-4 text-indigo-500" /> Export PX
              </button>
              <button
                onClick={shareProject}
                className="flex items-center gap-2 px-5 py-2.5 bg-zinc-900 border border-zinc-800 rounded-xl text-[10px] font-black text-zinc-300 hover:text-white transition-all uppercase tracking-widest"
              >
                <Share2 className="w-4 h-4 text-indigo-500" /> Share
              </button>
            </div>
          </div>

          <AnimatePresence mode="wait">
            {!layout ? (
              <motion.div
                key="empty"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.05 }}
                className="aspect-video w-full rounded-[3.5rem] border border-dashed border-zinc-900 flex flex-col items-center justify-center text-zinc-800 space-y-6 bg-gradient-to-b from-transparent to-zinc-900/10"
              >
                <div className="w-32 h-32 rounded-full border border-zinc-900 flex items-center justify-center shadow-inner">
                  <BoxIcon className="w-12 h-12 opacity-10" />
                </div>
                <div className="text-center">
                  <p className="text-sm font-black tracking-[0.3em] opacity-10 uppercase">System Idle</p>
                  <p className="text-[10px] opacity-10 font-bold italic mt-1">Submit configuration to proceed</p>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="results"
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                className="grid grid-cols-1 gap-12"
              >
                {/* 2D Blueprint Stage */}
                <div className="bg-[#0f0f12] rounded-[3.5rem] border border-zinc-800/50 shadow-2xl p-1.5 overflow-hidden relative">
                  <div className="absolute top-10 left-10 py-2.5 px-5 bg-black/60 backdrop-blur-xl rounded-full border border-zinc-800/40 flex items-center gap-3 z-10 shadow-xl">
                    <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
                    <span className="text-[9px] font-black text-zinc-300 uppercase tracking-[0.2em]">Blueprint Preview</span>
                  </div>

                  <div ref={blueprintRef} className="aspect-[4/3] w-full min-h-[550px] bg-[#0a0a0c] rounded-[3rem] flex items-center justify-center p-8 lg:p-24 overflow-hidden relative group">
                    {/* Architectural Grid Background */}
                    <div className="absolute inset-0 opacity-[0.04] pointer-events-none" style={{ backgroundImage: "radial-gradient(#fff 1px, transparent 1px)", backgroundSize: "40px 40px" }} />
                    <div className="absolute inset-0 opacity-[0.02] pointer-events-none" style={{ backgroundImage: "linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)", backgroundSize: "100px 100px" }} />

                    <div
                      className="relative bg-[#0d0d10] border-2 border-zinc-800 shadow-[0_0_150px_rgba(0,0,0,0.8)] transition-all duration-1000 group-hover:scale-[1.01] flex items-center justify-center"
                      style={{
                        width: `${layout.plot.w * 10}px`,
                        height: `${layout.plot.h * 10}px`,
                        maxWidth: "100%",
                        aspectRatio: `${layout.plot.w} / ${layout.plot.h}`
                      }}
                    >
                      {Object.entries(layout.placed).map(([key, [x, y, w, h]]) => {
                        const room = layout.rooms.find(r => r.key === key);
                        return (
                          <motion.div
                            key={key}
                            layoutId={key}
                            className="absolute border border-black/80 flex flex-col items-center justify-center group/room transition-all duration-500"
                            style={{
                              left: `${x * 10}px`,
                              top: `${y * 10}px`,
                              width: `${w * 10}px`,
                              height: `${h * 10}px`,
                              backgroundColor: room?.floor_color || "#eee"
                            }}
                          >
                            <span className="text-zinc-900 text-[10px] font-black px-2 text-center leading-tight truncate w-full mix-blend-multiply opacity-70">{room?.name}</span>
                            <span className="text-zinc-900 text-[8px] font-black opacity-30 mix-blend-multiply italic">{room?.w}x{room?.h}</span>
                          </motion.div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Confirm & 3D Action */}
                {!plotlyData ? (
                  <div className="flex justify-center pb-12">
                    <button
                      onClick={generate3D}
                      className="group flex items-center gap-5 bg-indigo-600 px-12 py-7 rounded-[2rem] font-black text-xs tracking-[0.2em] text-white shadow-[0_20px_50px_rgba(79,70,229,0.3)] hover:bg-indigo-500 transition-all scale-100 hover:scale-105 active:scale-95 uppercase"
                    >
                      <BoxIcon className="w-6 h-6" />
                      Generate Interactive 3D
                      <ChevronRight className="w-5 h-5 opacity-40 group-hover:translate-x-2 transition-transform" />
                    </button>
                  </div>
                ) : (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-[#0f0f12] rounded-[3.5rem] border border-zinc-800/50 shadow-2xl p-10 lg:p-14 space-y-10"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-5">
                        <div className="p-4 bg-indigo-600/10 rounded-2xl border border-indigo-500/20 shadow-inner">
                          <Layers className="w-7 h-7 text-indigo-400" />
                        </div>
                        <div>
                          <h3 className="text-2xl font-black text-white tracking-tight uppercase tracking-tighter">Dollhouse Model</h3>
                          <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest mt-1 italic">Real-time Volumetric Simulation</p>
                        </div>
                      </div>
                      <div className="px-5 py-2.5 bg-indigo-600 text-white rounded-full text-[9px] font-black uppercase tracking-[0.2em] shadow-lg shadow-indigo-600/20">
                        Live GL
                      </div>
                    </div>

                    <div className="h-[750px] w-full bg-[#0a0a0c] rounded-[3rem] overflow-hidden border border-zinc-800/50 relative shadow-2xl group">
                      <Plot
                        data={plotlyData.data}
                        layout={{
                          ...plotlyData.layout,
                          autosize: true,
                          width: undefined,
                          height: undefined,
                          paper_bgcolor: "rgba(0,0,0,0)",
                          plot_bgcolor: "rgba(0,0,0,0)",
                          font: { color: "#ccc", family: "Inter", size: 10 },
                          scene: {
                            ...plotlyData.layout.scene,
                            bgcolor: "rgba(10,10,12,1)",
                            xaxis: { ...plotlyData.layout.scene.xaxis, gridcolor: "#2e2e33", zerolinecolor: "#444", title: { font: { size: 10, color: "#666" } } },
                            yaxis: { ...plotlyData.layout.scene.yaxis, gridcolor: "#2e2e33", zerolinecolor: "#444", title: { font: { size: 10, color: "#666" } } },
                            zaxis: { ...plotlyData.layout.scene.zaxis, gridcolor: "#2e2e33", zerolinecolor: "#444", title: { font: { size: 10, color: "#666" } } },
                          }
                        }}
                        useResizeHandler={true}
                        style={{ width: "100%", height: "100%" }}
                        config={{
                          displayModeBar: true,
                          scrollZoom: true,
                          responsive: true,
                          toImageButtonOptions: {
                            format: "png",
                            filename: "CivilPlan_3D",
                            height: 1000,
                            width: 1500,
                            scale: 2
                          }
                        }}
                      />
                    </div>
                  </motion.div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Global CSS for custom scrollbar */}
      <style dangerouslySetInnerHTML={{
        __html: `
        .custom-scrollbar::-webkit-scrollbar { width: 5px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #1a1a1e; border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #222; }
      `}} />
    </div>
  );
};

export default App;
