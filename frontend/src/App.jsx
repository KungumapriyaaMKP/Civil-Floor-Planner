import React, { useState, useRef } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import {
  Box,
  Mic,
  MicOff,
  Layout,
  Box as BoxIcon,
  ChevronRight,
  Plus,
  Trash2,
  Terminal,
  Activity,
  Maximize2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = window.location.hostname === "localhost"
  ? "http://localhost:7860/api"
  : "/api";

const App = () => {
  const [plotSize, setPlotSize] = useState("40x30");
  const [roomText, setRoomText] = useState("Master Bedroom, 14, 12, top-left\nLiving, 20, 15, center\nKitchen, 12, 10, bottom-right\nBath, 8, 6, any");
  const [layout, setLayout] = useState(null);
  const [plotlyData, setPlotlyData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const generateLayout = async () => {
    setLoading(true);
    try {
      const resp = await axios.post(`${API_BASE}/generate`, {
        plot_size: plotSize,
        room_text: roomText
      });
      setLayout(resp.data);
      setPlotlyData(null); // Clear 3D till confirmed
    } catch (err) {
      alert("Error generating layout: " + err.message);
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
      alert("Error generating 3D: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorderRef.current = new MediaRecorder(stream);
    audioChunksRef.current = [];

    mediaRecorderRef.current.ondataavailable = (e) => {
      audioChunksRef.current.push(e.data);
    };

    mediaRecorderRef.current.onstop = async () => {
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
      const formData = new FormData();
      formData.append('file', audioBlob, 'voice.wav');

      try {
        const resp = await axios.post(`${API_BASE}/transcribe`, formData);
        setRoomText(prev => prev + "\n" + resp.data.parsed);
      } catch (err) {
        console.error("Transcription failed", err);
      }
    };

    mediaRecorderRef.current.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      mediaRecorderRef.current.stream.getTracks().forEach(t => t.stop());
    }
  };

  return (
    <div className="flex h-screen w-full bg-[#f8fafc] overflow-hidden text-slate-800 font-sans">
      {/* Sidebar */}
      <div className="w-96 bg-white border-r border-slate-200 flex flex-col shadow-xl z-10">
        <div className="p-6 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2 mb-1">
            <div className="bg-indigo-600 p-2 rounded-lg">
              <BoxIcon className="text-white w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900">CivilPlan AI</h1>
          </div>
          <p className="text-xs text-slate-400 font-medium tracking-wide uppercase">Architectural Engine v2.0</p>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <section>
            <label className="text-xs font-bold text-slate-500 uppercase flex items-center gap-1.5 mb-2">
              <Maximize2 className="w-3.5 h-3.5" /> Site Plot Size (ft)
            </label>
            <input
              value={plotSize}
              onChange={(e) => setPlotSize(e.target.value)}
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none transition-all font-medium"
              placeholder="e.g. 50x40"
            />
          </section>

          <section>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-slate-500 uppercase flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5" /> Room Specifications
              </label>
              <button
                onMouseDown={startRecording}
                onMouseUp={stopRecording}
                className={`p-2 rounded-full transition-all ${isRecording ? 'bg-red-100 text-red-600 animate-pulse' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}
                title="Hold to speak"
              >
                {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
              </button>
            </div>
            <textarea
              value={roomText}
              onChange={(e) => setRoomText(e.target.value)}
              className="w-full h-48 px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none transition-all text-sm font-mono leading-relaxed"
              placeholder="Name, W, H, Position..."
            />
            <p className="text-[10px] text-slate-400 mt-2 px-1">Tip: "Living Room, 20, 15, center"</p>
          </section>

          <button
            onClick={generateLayout}
            disabled={loading}
            className="w-full py-4 bg-slate-900 border border-slate-800 text-white rounded-2xl font-bold hover:bg-black transition-all flex items-center justify-center gap-2 group shadow-lg shadow-slate-200 hover:shadow-indigo-500/10 active:scale-[0.98]"
          >
            {loading ? <Activity className="w-5 h-5 animate-spin" /> : <Layout className="w-5 h-5 group-hover:rotate-12 transition-transform" />}
            Generate Layout
            <ChevronRight className="w-4 h-4 opacity-30" />
          </button>
        </div>

        {layout && (
          <div className="p-6 bg-slate-50 border-t border-slate-100 space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-slate-500 font-medium">Efficiency Score</span>
              <span className="text-indigo-600 font-bold">{layout.efficiency}%</span>
            </div>
            <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${layout.efficiency}%` }}
                className="h-full bg-indigo-600"
              />
            </div>
          </div>
        )}
      </div>

      {/* Main Preview Area */}
      <div className="flex-1 overflow-y-auto bg-[#f8fafc] flex flex-col">
        {!layout ? (
          <div className="flex-1 flex flex-col items-center justify-center opacity-40">
            <BoxIcon className="w-24 h-24 text-slate-200 mb-6" />
            <h2 className="text-2xl font-bold text-slate-400">Project Workspace</h2>
            <p className="text-slate-400 font-medium mt-2 text-center max-w-sm px-12">Set your plot size and rooms on the left to begin your architectural journey.</p>
          </div>
        ) : (
          <div className="p-8 space-y-8 max-w-6xl mx-auto w-full">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white p-2 rounded-[2rem] shadow-2xl shadow-slate-200/50 border border-slate-100 overflow-hidden relative"
            >
              <div className="absolute top-6 left-8 bg-white/80 backdrop-blur px-3 py-1 rounded-full border border-slate-100 text-[10px] font-bold text-slate-500 uppercase tracking-widest z-10 shadow-sm">
                2D Blueprint Preview
              </div>

              <div className="flex items-center justify-center bg-slate-50/50 rounded-[1.5rem] py-12 px-6">
                <div
                  className="relative bg-white border-2 border-slate-400 shadow-sm transition-all duration-700 hover:shadow-2xl hover:scale-[1.01]"
                  style={{
                    width: `${layout.plot.w * 10}px`,
                    height: `${layout.plot.h * 10}px`,
                    maxWidth: '100%',
                    aspectRatio: `${layout.plot.w} / ${layout.plot.h}`
                  }}
                >
                  {Object.entries(layout.placed).map(([key, [x, y, w, h]]) => {
                    const room = layout.rooms.find(r => r.key === key);
                    return (
                      <div
                        key={key}
                        className="absolute border border-black/40 flex flex-col items-center justify-center text-[8px] font-bold overflow-hidden transition-all duration-500"
                        style={{
                          left: `${x * 10}px`,
                          top: `${y * 10}px`,
                          width: `${w * 10}px`,
                          height: `${h * 10}px`,
                          backgroundColor: room?.floor_color || '#eee'
                        }}
                      >
                        <span className="opacity-70 truncate px-1">{room?.name}</span>
                        <span className="text-[6px] opacity-40">{room?.w}x{room?.h}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </motion.div>

            <AnimatePresence>
              {!plotlyData ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex justify-center"
                >
                  <button
                    onClick={generate3D}
                    className="flex items-center gap-3 px-8 py-5 bg-indigo-600 text-white rounded-full font-bold hover:bg-indigo-700 transition-all shadow-xl shadow-indigo-400/20 active:scale-[0.98] group"
                  >
                    <BoxIcon className="w-5 h-5" />
                    Confirm & Build 3D Model
                    <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </button>
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-white p-6 rounded-[2rem] shadow-2xl border border-slate-100 flex flex-col"
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest px-2">3D Dollhouse Visualization</h3>
                    <div className="bg-indigo-100 text-indigo-600 px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-tighter">Interactive</div>
                  </div>
                  <div className="h-[500px] w-full bg-slate-50 rounded-[1.5rem] overflow-hidden flex items-center justify-center border border-dashed border-slate-200">
                    <Plot
                      data={plotlyData.data}
                      layout={{
                        ...plotlyData.layout,
                        autosize: true,
                        width: undefined,
                        height: undefined
                      }}
                      useResizeHandler={true}
                      style={{ width: '100%', height: '100%' }}
                      config={{
                        displayModeBar: false,
                        scrollZoom: true
                      }}
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
