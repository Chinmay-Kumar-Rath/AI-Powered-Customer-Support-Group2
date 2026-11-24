import React from 'react';
import {BrowserRouter, Routes, Route, Navigate} from 'react-router-dom';
import {AuthProvider, useAuth} from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import AppShell from './components/AppShell';
import {Login,Register} from './pages/AuthPages';
import EmployeeDashboard from './pages/EmployeeDashboard';
import EmployeeTickets from './pages/EmployeeTickets';
import CreateTicket from './pages/CreateTicket';
import TicketDetail from './pages/TicketDetail';
import KnowledgeBase from './pages/KnowledgeBase';
import AdminDashboard from './pages/AdminDashboard';
import AdminTickets from './pages/AdminTickets';
import AdminTicketDetail from './pages/AdminTicketDetail';
import RagMetrics from './pages/RagMetrics';
function Home(){const{user,loading}=useAuth();if(loading)return <div className="full-screen-center"><div className="loader-ring"/>Loading SupportPilot…</div>;return <Navigate to={user?(user.role==='employee'?'/employee':'/admin'):'/login'} replace/>}
export default function App(){return <AuthProvider><BrowserRouter><Routes><Route path="/" element={<Home/>}/><Route path="/login" element={<Login/>}/><Route path="/register" element={<Register/>}/><Route element={<ProtectedRoute roles={['employee']}/>}><Route element={<AppShell/>}><Route path="/employee" element={<EmployeeDashboard/>}/><Route path="/employee/tickets" element={<EmployeeTickets/>}/><Route path="/employee/tickets/:id" element={<TicketDetail/>}/><Route path="/employee/create-ticket" element={<CreateTicket/>}/><Route path="/employee/kb" element={<KnowledgeBase/>}/></Route></Route><Route element={<ProtectedRoute roles={['admin','engineer']}/>}><Route element={<AppShell/>}><Route path="/admin" element={<AdminDashboard/>}/><Route path="/admin/tickets" element={<AdminTickets/>}/><Route path="/admin/tickets/:id" element={<AdminTicketDetail/>}/><Route path="/admin/kb" element={<KnowledgeBase/>}/><Route path="/admin/rag" element={<RagMetrics/>}/></Route></Route><Route path="*" element={<Navigate to="/" replace/>}/></Routes></BrowserRouter></AuthProvider>}
