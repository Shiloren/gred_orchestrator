import React, { useState } from 'react';
import { Save, Plus, Trash2, AlertCircle } from 'lucide-react';
import { EvalDataset, EvalCase } from '../../types';

interface EvalDatasetEditorProps {
    onSave: (dataset: EvalDataset) => Promise<void>;
    onCancel: () => void;
    initialData?: EvalDataset;
    workflowId?: string;
}

export const EvalDatasetEditor: React.FC<EvalDatasetEditorProps> = ({
    onSave,
    onCancel,
    initialData,
    workflowId
}) => {
    const [name, setName] = useState(initialData?.name || '');
    const [description, setDescription] = useState(initialData?.description || '');
    // Initialize with structured empty state
    const [cases, setCases] = useState<EvalCase[]>(initialData?.cases || [{
        input_state: { prompt: '' },
        expected_state: { content: '' }
    }]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleAddCase = () => {
        setCases([...cases, { input_state: { prompt: '' }, expected_state: { content: '' } }]);
    };

    const handleRemoveCase = (index: number) => {
        if (cases.length > 1) {
            setCases(cases.filter((_, i) => i !== index));
        }
    };

    const handleCaseChange = (index: number, type: 'input' | 'expected', value: string) => {
        const newCases = [...cases];
        if (type === 'input') {
            newCases[index] = { ...newCases[index], input_state: { ...newCases[index].input_state, prompt: value } };
        } else {
            newCases[index] = { ...newCases[index], expected_state: { ...newCases[index].expected_state, content: value } };
        }
        setCases(newCases);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!name.trim()) {
            setError('Dataset name is required');
            return;
        }

        if (cases.some(c => !c.input_state?.prompt)) {
            setError('All cases must have an input prompt');
            return;
        }

        setIsSubmitting(true);
        try {
            const dataset: EvalDataset = {
                ...initialData,
                workflow_id: workflowId || initialData?.workflow_id || 'default',
                name,
                description,
                cases
            };
            await onSave(dataset);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to save dataset');
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-8">
            <div className="bg-[#1c1c1e] w-full max-w-4xl max-h-[90vh] rounded-2xl border border-[#2c2c2e] shadow-2xl flex flex-col overflow-hidden">
                {/* Header */}
                <div className="p-6 border-b border-[#2c2c2e] bg-[#141414]">
                    <h2 className="text-xl font-bold text-[#f5f5f7]">
                        {initialData ? 'Clone / Edit Dataset' : 'Create New Dataset'}
                    </h2>
                    <p className="text-sm text-[#86868b] mt-1">
                        {initialData
                            ? 'Create a new dataset version based on this one. All saves create new entries.'
                            : 'Define golden cases (inputs and expected outputs) for regression testing.'}
                    </p>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6">
                    {/* Metadata */}
                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs font-bold text-[#86868b] uppercase mb-2">Dataset Name</label>
                            <input
                                type="text"
                                value={name}
                                onChange={e => setName(e.target.value)}
                                className="w-full bg-[#000000] border border-[#2c2c2e] rounded-lg px-4 py-2 text-[#f5f5f7] focus:border-[#0a84ff] outline-none transition-colors"
                                placeholder="e.g. Authentication Happy Paths"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-[#86868b] uppercase mb-2">Description</label>
                            <textarea
                                value={description}
                                onChange={e => setDescription(e.target.value)}
                                className="w-full bg-[#000000] border border-[#2c2c2e] rounded-lg px-4 py-2 text-[#f5f5f7] focus:border-[#0a84ff] outline-none transition-colors h-20 resize-none"
                                placeholder="Describe the purpose of this dataset..."
                            />
                        </div>
                    </div>

                    {/* Cases */}
                    <div>
                        <div className="flex items-center justify-between mb-4">
                            <label className="text-xs font-bold text-[#86868b] uppercase">Test Cases ({cases.length})</label>
                            <button
                                type="button"
                                onClick={handleAddCase}
                                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0a84ff]/10 text-[#0a84ff] hover:bg-[#0a84ff]/20 text-xs font-medium transition-colors"
                            >
                                <Plus size={14} />
                                Add Case
                            </button>
                        </div>

                        <div className="space-y-4">
                            {cases.map((c, idx) => (
                                <div key={idx} className="bg-[#000000] border border-[#2c2c2e] rounded-xl p-4 relative group">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-[10px] text-[#86868b] font-bold uppercase mb-1">Input Prompt</label>
                                            <textarea
                                                value={c.input_state?.prompt || JSON.stringify(c.input_state)}
                                                onChange={e => handleCaseChange(idx, 'input', e.target.value)}
                                                className="w-full bg-[#141414] border border-[#2c2c2e] rounded-lg p-3 text-sm text-[#f5f5f7] font-mono h-32 focus:border-[#0a84ff] outline-none resize-none"
                                                placeholder="User prompt or input..."
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-[10px] text-[#86868b] font-bold uppercase mb-1">Expected Output</label>
                                            <textarea
                                                value={c.expected_state?.content || JSON.stringify(c.expected_state)}
                                                onChange={e => handleCaseChange(idx, 'expected', e.target.value)}
                                                className="w-full bg-[#141414] border border-[#2c2c2e] rounded-lg p-3 text-sm text-[#f5f5f7] font-mono h-32 focus:border-[#32d74b] outline-none resize-none"
                                                placeholder="Expected agent response..."
                                            />
                                        </div>
                                    </div>

                                    {cases.length > 1 && (
                                        <button
                                            onClick={() => handleRemoveCase(idx)}
                                            className="absolute top-2 right-2 p-1.5 text-[#86868b] hover:text-[#ff453a] hover:bg-[#ff453a]/10 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
                                            title="Remove case"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-[#2c2c2e] bg-[#141414] flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        {error && (
                            <>
                                <AlertCircle size={16} className="text-[#ff453a]" />
                                <span className="text-sm text-[#ff453a]">{error}</span>
                            </>
                        )}
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            type="button"
                            onClick={onCancel}
                            disabled={isSubmitting}
                            className="px-4 py-2 rounded-lg text-[#86868b] hover:text-[#f5f5f7] hover:bg-[#2c2c2e] transition-colors text-sm font-medium"
                        >
                            Cancel
                        </button>
                        <button
                            type="button"
                            onClick={handleSubmit}
                            disabled={isSubmitting}
                            className="flex items-center gap-2 px-6 py-2 rounded-lg bg-[#0a84ff] hover:bg-[#0071e3] text-white transition-colors text-sm font-bold shadow-lg shadow-[#0a84ff]/20 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isSubmitting ? 'Saving...' : (
                                <>
                                    <Save size={16} />
                                    {initialData ? 'Save as New' : 'Save Dataset'}
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
