import React, { useState, useEffect } from 'react';
import { Languages, Globe, Save, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import { useTerminology } from '../hooks/useTerminology';

export default function AdminTerminology() {
  const { t, language, changeLanguage } = useTerminology();
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadKeys() {
      try {
        setLoading(true);
        const res = await api.get('/lookups/translations');
        setKeys(Array.isArray(res) ? res : []);
      } catch (err) {
        // Fallback default list for demo
        setKeys([
          { id: '1', key: 'relationship.mother', english: 'Mother', translation: 'Nikāwiy (Mother)', is_active: true },
          { id: '2', key: 'relationship.father', english: 'Father', translation: 'Nōhtāwiy (Father)', is_active: true },
          { id: '3', key: 'relationship.grandmother', english: 'Grandmother', translation: 'Nōhkom (Grandmother)', is_active: true },
          { id: '4', key: 'relationship.grandfather', english: 'Grandfather', translation: 'Nimōsom (Grandfather)', is_active: true },
          { id: '5', key: 'relationship.child', english: 'Child', translation: 'Awāsis (Child)', is_active: true },
          { id: '6', key: 'program.sacred_wolf', english: 'Sacred Wolf Lodge', translation: 'Sacred Wolf Lodge (Miyowāwisin)', is_active: true },
        ]);
      } finally {
        setLoading(false);
      }
    }
    loadKeys();
  }, []);

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b pb-5">
        <div>
          <div className="flex items-center space-x-2">
            <Languages className="h-6 w-6 text-indigo-600" />
            <h1 className="text-2xl font-bold text-slate-900">Cultural Terminology & Cree Language Settings</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Application language resolver. Status: REQUIRES CRBCL LANGUAGE VALIDATION for official Cree dictionary entries.
          </p>
        </div>

        <div className="flex items-center space-x-3 bg-slate-100 p-1.5 rounded-lg border">
          <Globe className="h-4 w-4 text-slate-500 ml-1" />
          <span className="text-xs font-semibold text-slate-700">UI Preference:</span>
          <button
            onClick={() => changeLanguage('en')}
            className={`px-3 py-1 text-xs font-medium rounded ${language === 'en' ? 'bg-white shadow text-indigo-700' : 'text-slate-600'}`}
          >
            English
          </button>
          <button
            onClick={() => changeLanguage('cr')}
            className={`px-3 py-1 text-xs font-medium rounded ${language === 'cr' ? 'bg-white shadow text-indigo-700' : 'text-slate-600'}`}
          >
            Cree Terms (Preview)
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border p-6 space-y-4">
        <div className="flex items-center justify-between border-b pb-3">
          <h2 className="text-base font-bold text-slate-900">Approved Cultural Terminology Keys</h2>
          <span className="text-xs text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-full font-medium">
            Status: REQUIRES CRBCL LANGUAGE VALIDATION
          </span>
        </div>

        {loading ? (
          <div className="text-center py-8 text-slate-500 text-sm">Loading terminology dictionary...</div>
        ) : (
          <div className="divide-y divide-slate-200">
            {keys.map(k => (
              <div key={k.id} className="py-3 flex flex-col md:flex-row md:items-center justify-between gap-3 text-sm">
                <div>
                  <code className="text-xs bg-slate-100 px-2 py-0.5 rounded text-indigo-800 font-mono">{k.key}</code>
                  <p className="text-xs text-slate-500 mt-0.5">Standard English: <span className="font-semibold text-slate-800">{k.english}</span></p>
                </div>
                <div className="flex items-center space-x-3">
                  <input
                    type="text"
                    defaultValue={k.translation}
                    className="rounded-md border-slate-300 border text-xs p-1.5 w-64 shadow-sm"
                  />
                  <button className="inline-flex items-center px-2.5 py-1 text-xs border border-slate-300 rounded text-slate-700 hover:bg-slate-50">
                    <Save className="h-3.5 w-3.5 mr-1 text-slate-500" />
                    Save
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
