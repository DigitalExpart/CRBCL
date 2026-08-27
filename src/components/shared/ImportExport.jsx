import React, { useRef } from "react";
import * as XLSX from "xlsx";
import { Download, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * ImportExport component
 * @param {Object[]} data - Array of records to export
 * @param {string} filename - Base filename (without extension)
 * @param {string[]} exportFields - Keys to include in export (in order)
 * @param {Object} fieldLabels - Map of key -> column header label
 * @param {Function} onImport - Called with array of row objects from imported file
 */
export default function ImportExport({ data = [], filename = "export", exportFields, fieldLabels = {}, onImport }) {
  const fileInputRef = useRef(null);

  const handleExport = () => {
    const rows = data.map(record => {
      const row = {};
      const keys = exportFields || Object.keys(record);
      keys.forEach(key => {
        const label = fieldLabels[key] || key;
        const val = record[key];
        row[label] = Array.isArray(val) ? val.join(", ") : (val ?? "");
      });
      return row;
    });

    const ws = XLSX.utils.json_to_sheet(rows);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Data");
    XLSX.writeFile(wb, `${filename}_${new Date().toISOString().split("T")[0]}.xlsx`);
  };

  const handleImport = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      const wb = XLSX.read(evt.target.result, { type: "array" });
      const ws = wb.Sheets[wb.SheetNames[0]];
      const rows = XLSX.utils.sheet_to_json(ws);

      // Reverse-map labels back to field keys if fieldLabels provided
      const reverseLabels = Object.fromEntries(Object.entries(fieldLabels).map(([k, v]) => [v, k]));
      const mapped = rows.map(row => {
        const record = {};
        Object.entries(row).forEach(([col, val]) => {
          const key = reverseLabels[col] || col;
          record[key] = val === "" ? undefined : val;
        });
        return record;
      });

      onImport && onImport(mapped);
    };
    reader.readAsArrayBuffer(file);
    e.target.value = "";
  };

  return (
    <div className="flex items-center gap-2">
      <Button variant="outline" size="sm" onClick={handleExport}>
        <Download className="w-4 h-4 mr-1.5" /> Export
      </Button>
      {onImport && (
        <>
          <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()}>
            <Upload className="w-4 h-4 mr-1.5" /> Import
          </Button>
          <input ref={fileInputRef} type="file" accept=".xlsx,.xls,.csv" className="hidden" onChange={handleImport} />
        </>
      )}
    </div>
  );
}