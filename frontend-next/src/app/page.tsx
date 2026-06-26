import LandingNavbar from '@/components/Landing/LandingNavbar';
import HeroSection from '@/components/Landing/HeroSection';
import StatsStrip from '@/components/Landing/StatsStrip';
import FeaturesSection from '@/components/Landing/FeaturesSection';
import BacktestSection from '@/components/Landing/BacktestSection';
import AboutSection from '@/components/Landing/AboutSection';
import ContactSection from '@/components/Landing/ContactSection';
import LandingFooter from '@/components/Landing/LandingFooter';

export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <LandingNavbar />
      <HeroSection />
      <StatsStrip />
      <FeaturesSection />
      <BacktestSection />
      <AboutSection />
      <ContactSection />
      <LandingFooter />
    </div>
  );
}
