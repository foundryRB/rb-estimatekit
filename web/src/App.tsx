import { Routes, Route } from 'react-router-dom';
import { AmbientField } from '@/views/atoms/AmbientField';
import { HomePage } from '@/views/pages/HomePage';
import { WorkspacePage } from '@/views/pages/WorkspacePage';

/**
 * Root application component.
 *
 * Routes:
 *   /                   → Home  (create or open a project)
 *   /projects/:slug     → Workspace  (IDE for editing/generating)
 */
export default function App() {
    return (
        <>
            <AmbientField />
            <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/projects/:slug" element={<WorkspacePage />} />
            </Routes>
        </>
    );
}
