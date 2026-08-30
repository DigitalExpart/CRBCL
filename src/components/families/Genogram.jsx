import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { User, Users, Heart, ArrowRight, Home, Shield, Sparkles } from "lucide-react";

export default function Genogram({ genogramData, onSelectPerson }) {
  const [selectedNode, setSelectedNode] = useState(null);

  if (!genogramData || !genogramData.nodes || genogramData.nodes.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-12 text-center text-muted-foreground">
          <Users className="w-12 h-12 mx-auto mb-3 opacity-40 text-primary" />
          <p className="font-medium">No Genogram Data Recorded Yet</p>
          <p className="text-sm mt-1">Add family members and define kinship relationships to generate the visual family tree.</p>
        </CardContent>
      </Card>
    );
  }

  const { nodes = [], edges = [], households = [] } = genogramData;

  const handleNodeClick = (node) => {
    setSelectedNode(node);
    if (onSelectPerson) {
      onSelectPerson(node.data);
    }
  };

  return (
    <div className="space-y-6">
      {/* Genogram Canvas Container */}
      <div className="relative bg-slate-950/60 rounded-xl border border-border/80 p-6 min-h-[420px] overflow-x-auto">
        <div className="flex items-center justify-between mb-4 border-b border-border/50 pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span className="text-sm font-semibold text-foreground">Kinship & Family Genogram</span>
            <Badge variant="outline" className="text-xs">{nodes.length} Individuals</Badge>
          </div>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span> Male</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-pink-500"></span> Female</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span> Non-Binary / Two-Spirit</span>
          </div>
        </div>

        {/* Nodes Grid Layout */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {nodes.map((node) => {
            const isSelected = selectedNode?.id === node.id;
            const genderColor =
              node.data.gender === "Male" ? "border-blue-500/50 bg-blue-950/20" :
              node.data.gender === "Female" ? "border-pink-500/50 bg-pink-950/20" :
              "border-purple-500/50 bg-purple-950/20";

            return (
              <div
                key={node.id}
                onClick={() => handleNodeClick(node)}
                className={`cursor-pointer rounded-lg border-2 p-3.5 transition-all hover:scale-[1.02] hover:shadow-lg ${genderColor} ${
                  isSelected ? "ring-2 ring-primary ring-offset-2 ring-offset-background border-primary" : ""
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-sm">
                      {node.data.fullName?.charAt(0) || <User className="w-4 h-4" />}
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-foreground leading-tight">{node.data.fullName}</h4>
                      {node.data.preferredName && (
                        <p className="text-xs text-muted-foreground italic">"{node.data.preferredName}"</p>
                      )}
                    </div>
                  </div>
                  <Badge variant="secondary" className="text-[10px] uppercase font-semibold">
                    {node.data.role}
                  </Badge>
                </div>

                <div className="mt-3 pt-2.5 border-t border-border/40 grid grid-cols-2 gap-1 text-[11px] text-muted-foreground">
                  <div>
                    <span className="font-medium text-foreground/80">DOB:</span> {node.data.dateOfBirth || "N/A"}
                  </div>
                  <div>
                    <span className="font-medium text-foreground/80">Gender:</span> {node.data.gender}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Directional Relationships List */}
        {edges.length > 0 && (
          <div className="mt-6 pt-4 border-t border-border/50">
            <h5 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-1.5">
              <Heart className="w-3.5 h-3.5 text-rose-400" /> Kinship & Interpersonal Connections
            </h5>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
              {edges.map((edge) => {
                const sourceNode = nodes.find(n => n.id === edge.source);
                const targetNode = nodes.find(n => n.id === edge.target);

                return (
                  <div key={edge.id} className="text-xs bg-muted/40 rounded-md p-2 flex items-center justify-between border border-border/40">
                    <span className="font-medium text-foreground truncate">{sourceNode?.data.fullName || "Person A"}</span>
                    <Badge variant="outline" className="text-[10px] mx-1 bg-background shrink-0 font-medium">
                      {edge.label}
                    </Badge>
                    <span className="font-medium text-foreground truncate">{targetNode?.data.fullName || "Person B"}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <Card className="bg-muted/30 border-primary/30 animate-in fade-in slide-in-from-top-2">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <User className="w-4 h-4 text-primary" /> {selectedNode.data.fullName}
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setSelectedNode(null)}>Close</Button>
            </div>
            <CardDescription>Kinship role: {selectedNode.data.role}</CardDescription>
          </CardHeader>
          <CardContent className="text-xs space-y-2">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <div><strong className="text-muted-foreground">Person ID:</strong> <span className="font-mono">{selectedNode.data.personId}</span></div>
              <div><strong className="text-muted-foreground">Date of Birth:</strong> {selectedNode.data.dateOfBirth || "Unknown"}</div>
              <div><strong className="text-muted-foreground">Gender:</strong> {selectedNode.data.gender}</div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
