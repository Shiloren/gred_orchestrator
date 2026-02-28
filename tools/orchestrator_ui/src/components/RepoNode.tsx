import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { FolderGit2 } from 'lucide-react';

export const RepoNode = memo(({ data, selected }: any) => {
    return (
        <div className={`
            px-4 py-3 rounded-xl bg-surface-1 border-2 transition-all duration-200 min-w-[160px]
            ${selected
                ? 'border-accent-purple shadow-[0_0_20px_rgba(94,92,230,0.3)]'
                : 'border-border-primary hover:border-accent-purple/40'}
        `}>
            <div className="flex items-center gap-3">
                <div className="relative">
                    <div className="w-9 h-9 rounded-lg bg-accent-purple/15 flex items-center justify-center">
                        <FolderGit2 size={18} className="text-accent-purple" />
                    </div>
                    <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-accent-trust border-2 border-surface-1" />
                </div>
                <div>
                    <div className="text-xs font-semibold text-text-primary">{data.label}</div>
                    <div className="text-[10px] text-text-secondary font-mono truncate max-w-[120px]">{data.path}</div>
                </div>
            </div>
            <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-accent-purple !border-surface-1 !border-2" />
        </div>
    );
});
