import { MaintenanceIsland } from './islands/system/MaintenanceIsland';

export default function App() {
    return (
        <div className="min-h-screen bg-[#f5f5f7] dark:bg-[#1d1d1f] font-sans antialiased">
            <div className="max-w-3xl mx-auto px-6 py-12">
                {/* Header */}
                <header className="mb-12 text-center">
                    <h1 className="text-3xl font-semibold text-[#1d1d1f] dark:text-white tracking-tight">
                        Repo Orchestrator
                    </h1>
                    <p className="text-sm text-[#86868b] mt-2">
                        Gred In Labs
                    </p>
                </header>

                {/* Main Content */}
                <main className="bg-white dark:bg-[#2d2d2d] rounded-2xl shadow-sm border border-[#d2d2d7] dark:border-[#424245] p-6">
                    <MaintenanceIsland />
                </main>

                {/* Footer */}
                <footer className="mt-8 text-center text-xs text-[#86868b]">
                    v1.0.0
                </footer>
            </div>
        </div>
    );
}
