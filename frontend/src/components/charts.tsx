"use client";

import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, BarChart, Bar, CartesianGrid, PieChart, Pie, Cell } from "recharts";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { motion } from "framer-motion";

const VIOLET_COLORS = ["#8a63f2", "#b4a5f5", "#d4c9fd", "#6d4ebd", "#e0d9ff"];

const TooltipStyle = {
  contentStyle: { background: "rgba(20,12,38,0.95)", border: "1px solid rgba(138,99,242,0.3)", borderRadius: "12px", color: "#f0eeff" },
  labelStyle: { color: "#b4a5f5" },
  cursor: { fill: "rgba(138,99,242,0.08)" },
};

export function ActivityChart({ data }: { data: any[] }) {
  return (
    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.4 }}>
      <Card className="glass-violet border-primary/20">
        <CardTitle className="text-white">Daily Activity</CardTitle>
        <CardContent className="mt-4 h-72">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="a1" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8a63f2" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#8a63f2" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="day" stroke="#9c8ec4" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#9c8ec4" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip {...TooltipStyle} />
              <Area type="monotone" dataKey="count" stroke="#8a63f2" strokeWidth={2.5} fillOpacity={1} fill="url(#a1)" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export function ConfidenceChart({ data }: { data: any[] }) {
  return (
    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.4, delay: 0.1 }}>
      <Card className="glass-violet border-primary/20">
        <CardTitle className="text-white">Confidence Buckets</CardTitle>
        <CardContent className="mt-4 h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(138,99,242,0.12)" />
              <XAxis dataKey="bucket" stroke="#9c8ec4" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#9c8ec4" fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip {...TooltipStyle} />
              <Bar dataKey="count" radius={[12,12,0,0]} fill="#8a63f2" opacity={0.85} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export function SourceChart({ data }: { data: any[] }) {
  return (
    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.4, delay: 0.2 }}>
      <Card className="glass-violet border-primary/20">
        <CardTitle className="text-white">Source Breakdown</CardTitle>
        <CardContent className="mt-4 h-72">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} dataKey="count" nameKey="source" innerRadius={65} outerRadius={95} paddingAngle={3} strokeWidth={0}>
                {data.map((_entry, index) => (
                  <Cell key={index} fill={VIOLET_COLORS[index % VIOLET_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip {...TooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </motion.div>
  );
}
