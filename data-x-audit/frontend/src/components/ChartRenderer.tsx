"use client";

import { 
  BarChart, Bar, 
  LineChart, Line, 
  AreaChart, Area, 
  PieChart, Pie, Cell,
  ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { ChartSpec } from '@/types/contracts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

interface ChartRendererProps {
  spec: ChartSpec;
}

const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export function ChartRenderer({ spec }: ChartRendererProps) {
  const { chart_type, title, data, x_axis, y_axis, series } = spec;

  const renderChart = () => {
    switch (chart_type) {
      case 'bar':
      case 'histogram':
        return (
          <BarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis 
              dataKey={x_axis.key} 
              label={{ value: x_axis.label, position: 'insideBottom', offset: -5 }} 
              fontSize={12}
            />
            <YAxis 
              label={{ value: y_axis?.label, angle: -90, position: 'insideLeft' }} 
              fontSize={12}
            />
            <Tooltip />
            <Legend verticalAlign="top" height={36} />
            {series.map((s, i) => (
              <Bar 
                key={s.key} 
                dataKey={s.key} 
                name={s.label} 
                fill={s.color_hint || COLORS[i % COLORS.length]} 
                radius={[4, 4, 0, 0]}
                barSize={chart_type === 'histogram' ? undefined : 20}
              />
            ))}
          </BarChart>
        );

      case 'line':
        return (
          <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey={x_axis.key} fontSize={12} />
            <YAxis fontSize={12} />
            <Tooltip />
            <Legend verticalAlign="top" height={36} />
            {series.map((s, i) => (
              <Line 
                key={s.key} 
                type="monotone" 
                dataKey={s.key} 
                name={s.label} 
                stroke={s.color_hint || COLORS[i % COLORS.length]} 
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
            ))}
          </LineChart>
        );

      case 'area':
        return (
          <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey={x_axis.key} fontSize={12} />
            <YAxis fontSize={12} />
            <Tooltip />
            <Legend verticalAlign="top" height={36} />
            {series.map((s, i) => (
              <Area 
                key={s.key} 
                type="monotone" 
                dataKey={s.key} 
                name={s.label} 
                stroke={s.color_hint || COLORS[i % COLORS.length]} 
                fill={s.color_hint || COLORS[i % COLORS.length]} 
                fillOpacity={0.3}
              />
            ))}
          </AreaChart>
        );

      case 'pie':
        return (
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey={series[0]?.key || 'value'}
              nameKey={x_axis.key}
              label
            >
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        );

      case 'scatter':
        return (
          <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <CartesianGrid />
            <XAxis type="number" dataKey={x_axis.key} name={x_axis.label} />
            <YAxis type="number" dataKey={y_axis?.key} name={y_axis?.label} />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
            <Legend verticalAlign="top" height={36} />
            {series.map((s, i) => (
              <Scatter 
                key={s.key} 
                name={s.label} 
                data={data} 
                fill={s.color_hint || COLORS[i % COLORS.length]} 
              />
            ))}
          </ScatterChart>
        );

      default:
        return (
          <div className="flex items-center justify-center h-full bg-muted/20 text-muted-foreground text-sm italic">
            Tipo de gráfico &quot;{chart_type}&quot; no soportado actualmente.
          </div>
        );
    }
  };

  return (
    <Card className="w-full">
      <CardHeader className="p-4">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent className="p-4 pt-0 h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
