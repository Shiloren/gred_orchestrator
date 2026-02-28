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
            <div className="bg-surface-2 w-full max-w-4xl max-h-[90vh] rounded-2xl border border-border-primary shadow-2xl flex flex-col overflow-hidden">
                {/* Header */}
                <div className="p-6 border-b border-border-primary bg-surface-1">
                    <h2 className="text-xl font-bold text-text-primary">
                        {initialData ? 'Clone / Edit Dataset' : 'Create New Dataset'}
                    </h2>
                    <p className="text-sm text-text-secondary mt-1">
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
                            <label className="block text-xs font-bold text-text-secondary uppercase mb-2">Dataset Name</label>
                            <input
                                type="text"
                                value={name}
                                onChange={e => setName(e.target.value)}
                                className="w-full bg-surface-0 border border-border-primary rounded-lg px-4 py-2 text-text-primary focus:border-accent-primary outline-none transition-colors"
                                placeholder="e.g. Authentication Happy Paths"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-text-secondary uppercase mb-2">Description</label>
                            <textarea
                                value={description}
                                onChange={e => setDescription(e.target.value)}
                                className="w-full bg-surface-0 border border-border-primary rounded-lg px-4 py-2 text-text-primary focus:border-accent-primary outline-none transition-colors h-20 resize-none"
                                placeholder="Describe the purpose of this dataset..."
                            />
                        </div>
                    </div>

                    {/* Cases */}
                    <div>
                        <div className="flex items-center justify-between mb-4">
                            <label className="text-xs font-bold text-text-secondary uppercase">Test Cases ({cases.length})</label>
                            <button
                                type="button"
                                onClick={handleAddCase}
                                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-accent-primary/10 text-accent-primary hover:bg-accent-primary/20 text-xs font-medium transition-colors"
                            >
                                <Plus size={14} />
                                Add Case
                            </button>
                        </div>

                        <div className="space-y-4">
                            {cases.map((c, idx) => (
                                <div key={idx} className="bg-surface-0 border border-border-primary rounded-xl p-4 relative group">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-[10px] text-text-secondary font-bold uppercase mb-1">Input Prompt</label>
                                            <textarea
                                                value={c.input_state?.prompt || JSON.stringify(c.input_state)}
                                                onChange={e => handleCaseChange(idx, 'input', e.target.value)}
                                                className="w-full bg-surface-1 border border-border-primary rounded-lg p-3 text-sm text-text-primary font-mono h-32 focus:border-accent-primary outline-none resize-none"
                                                placeholder="User prompt or input..."
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-[10px] text-text-secondary font-bold uppercase mb-1">Expected Output</label>
                                            <textarea
                                                value={c.expected_state?.content || JSON.stringify(c.expected_state)}
                                                onChange={e => handleCaseChange(idx, 'expected', e.target.value)}
                                                className="w-full bg-surface-1 border border-border-primary rounded-lg p-3 text-sm text-text-primary font-mono h-32 focus:border-accent-trust outline-none resize-none"
                                                placeholder="Expected agent response..."
                                            />
                                        </div>
                                    </div>

                                    {cases.length > 1 && (
                                        <button
                                            onClick={() => handleRemoveCase(idx)}
                                            className="absolute top-2 right-2 p-1.5 text-text-secondary hover:text-accent-alert hover:bg-accent-alert/10 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
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
                <div className="p-4 border-t border-border-primary bg-surface-1 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        {error && (
                            <>
                                <AlertCircle size={16} className="text-accent-alert" />
                                <span className="text-sm text-accent-alert">{error}</span>
                            </>
                        )}
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            type="button"
                            onClick={onCancel}
                            disabled={isSubmitting}
                            className="px-4 py-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-3 transition-colors text-sm font-medium"
                        >
                            Cancel
                        </button>
                        <button
                            type="button"
                            onClick={handleSubmit}
                            disabled={isSubmitting}
                            className="flex items-center gap-2 px-6 py-2 rounded-lg bg-accent-primary hover:bg-accent-primary/80 text-white transition-colors text-sm font-bold shadow-lg shadow-accent-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
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
