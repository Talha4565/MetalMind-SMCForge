import DashboardLayout from '@/components/Common/DashboardLayout';
import RiskMetrics from '@/components/Risk/RiskMetrics';

export default function RiskPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <RiskMetrics />
      </div>
    </DashboardLayout>
  );
}
