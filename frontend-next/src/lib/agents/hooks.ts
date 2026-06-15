'use client';

import { useState, useEffect, useCallback } from 'react';
import { agentOrchestrator } from './agent-orchestrator';
import { AgentTask, AgentRole, AgentMetrics } from './types';

/**
 * Hook to spawn and manage an agent task
 */
export function useAgentTask(agent: AgentRole, taskType: string) {
  const [task, setTask] = useState<AgentTask | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const spawn = useCallback(
    async (input: Record<string, unknown>) => {
      setIsLoading(true);
      setError(null);

      try {
        const newTask = await agentOrchestrator.spawnTask(agent, taskType, input);
        setTask(newTask);
        return newTask;
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMsg);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [agent, taskType]
  );

  const cancel = useCallback(async () => {
    if (task?.id) {
      try {
        await agentOrchestrator.cancelTask(task.id);
        setTask((prev) => (prev ? { ...prev, status: 'cancelled' } : null));
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMsg);
      }
    }
  }, [task]);

  return { task, spawn, cancel, isLoading, error };
}

/**
 * Hook to fetch and track agent metrics
 */
export function useAgentMetrics(agent: AgentRole) {
  const [metrics, setMetrics] = useState<AgentMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const data = await agentOrchestrator.getMetrics(agent);
        setMetrics(data);
      } catch (err) {
        console.error('Failed to fetch agent metrics:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMetrics();

    // Poll every 30 seconds
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, [agent]);

  return { metrics, isLoading };
}

/**
 * Hook to monitor all active tasks
 */
export function useActiveTasks() {
  const [tasks, setTasks] = useState<AgentTask[]>([]);

  useEffect(() => {
    const pollTasks = () => {
      const activeTasks = agentOrchestrator.getActiveTasks();
      setTasks(activeTasks);
    };

    pollTasks();
    const interval = setInterval(pollTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  return tasks;
}

/**
 * Hook to search agent memory
 */
export function useAgentMemory(namespace: string) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(
    async (query: string, limit = 10) => {
      setIsLoading(true);
      setError(null);

      try {
        const results = await agentOrchestrator.searchMemory(
          namespace,
          query,
          limit
        );
        return results;
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMsg);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [namespace]
  );

  const store = useCallback(
    async (key: string, value: unknown) => {
      setIsLoading(true);
      setError(null);

      try {
        await agentOrchestrator.storeMemory(namespace, key, value);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMsg);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [namespace]
  );

  return { search, store, isLoading, error };
}
