import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TrustBadge } from '../TrustBadge';
import { AgentQuestionCard } from '../AgentQuestionCard';
import { AgentQuestion } from '../../types';

describe('TrustBadge', () => {
    it('renders autonomous level correctly', () => {
        render(<TrustBadge level="autonomous" showLabel />);
        expect(screen.getByText(/autonomous/i)).toBeDefined();
    });

    it('renders supervised level correctly', () => {
        render(<TrustBadge level="supervised" showLabel />);
        expect(screen.getByText(/supervised/i)).toBeDefined();
    });

    it('renders restricted level correctly', () => {
        render(<TrustBadge level="restricted" showLabel />);
        expect(screen.getByText(/restricted/i)).toBeDefined();
    });
});

describe('AgentQuestionCard', () => {
    const mockQuestion: AgentQuestion = {
        id: 'q1',
        question: 'Is this correct?',
        context: 'Context info',
        timestamp: new Date().toISOString(),
        status: 'pending'
    };

    it('renders question and context', () => {
        render(
            <AgentQuestionCard
                question={mockQuestion}
                onAnswer={() => { }}
                onDismiss={() => { }}
            />
        );
        expect(screen.getByText(mockQuestion.question)).toBeDefined();
        expect(screen.getByText(mockQuestion.context!)).toBeDefined();
    });

    it('calls onAnswer when approve button is clicked', () => {
        const onAnswer = vi.fn();
        render(
            <AgentQuestionCard
                question={mockQuestion}
                onAnswer={onAnswer}
                onDismiss={() => { }}
            />
        );
        fireEvent.click(screen.getByText(/approve/i));
        expect(onAnswer).toHaveBeenCalledWith(mockQuestion.id, 'Approved');
    });

    it('calls onAnswer when reject button is clicked', () => {
        const onAnswer = vi.fn();
        render(
            <AgentQuestionCard
                question={mockQuestion}
                onAnswer={onAnswer}
                onDismiss={() => { }}
            />
        );
        fireEvent.click(screen.getByText(/reject/i));
        expect(onAnswer).toHaveBeenCalledWith(mockQuestion.id, 'Rejected');
    });

    it('calls onDismiss when escalate button is clicked', () => {
        const onDismiss = vi.fn();
        render(
            <AgentQuestionCard
                question={mockQuestion}
                onAnswer={() => { }}
                onDismiss={onDismiss}
            />
        );
        fireEvent.click(screen.getByText(/escalate/i));
        expect(onDismiss).toHaveBeenCalledWith(mockQuestion.id);
    });
});
