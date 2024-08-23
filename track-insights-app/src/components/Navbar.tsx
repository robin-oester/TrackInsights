import React from "react";

import { useTranslation } from "react-i18next";
import {
  Accordion, AccordionItem,
  Button, Dropdown, DropdownItem, DropdownMenu, DropdownTrigger, Image, Link, Navbar,
  NavbarBrand, NavbarContent, NavbarItem, NavbarMenu, NavbarMenuItem, NavbarMenuToggle
} from "@nextui-org/react";
import {
  Activity, ChevronDown, DEFlag, Flash, GBFlag, Lock, MoonIcon, Scale, Server,
  SunIcon, TagUser, WorldIcon
} from "./Icons.tsx";
import DarkModeSwitcher from "./DarkModeSwitcher.tsx";
import logo from '/logo_large.png';

const NavigationBar = () => {
  const { t, i18n } = useTranslation();

  const handleLanguageChange = (lang: string) => {
    void i18n.changeLanguage(lang);
  };

  const [isMenuOpen, setIsMenuOpen] = React.useState(false);

  const icons = {
    chevron: <ChevronDown fill="currentColor" size={16} />,
    scale: <Scale className="text-warning" fill="currentColor" size={30} />,
    lock: <Lock className="text-success" fill="currentColor" size={30} />,
    activity: <Activity className="text-secondary" fill="currentColor" size={30} />,
    flash: <Flash className="text-primary" fill="currentColor" size={30} />,
    server: <Server className="text-success" fill="currentColor" size={30} />,
    user: <TagUser className="text-danger" fill="currentColor" size={30} />,
    moon: <MoonIcon />,
    sun: <SunIcon />,
    enFlag: <GBFlag />,
    deFlag: <DEFlag />,
    world: <WorldIcon size={20} fill="currentColor" />,
  };

  const accItemClasses = {
    content: "py-0",
    trigger: "p-0"
  };

  return (
    <Navbar isMenuOpen={isMenuOpen} onMenuOpenChange={setIsMenuOpen} isBordered shouldHideOnScroll>
      <NavbarContent>
        <NavbarMenuToggle
          aria-label={isMenuOpen ? "Close menu" : "Open menu"}
          className="sm:hidden"
        />
        <Link href={"/overview"} color="foreground">
          <NavbarBrand>
            <Image src={logo} className="p-1" width={50}/>
            <p className="font-bold text-inherit">TrackInsights</p>
          </NavbarBrand>
        </Link>
      </NavbarContent>
      <NavbarContent className="hidden sm:flex gap-4" justify="center">
        <NavbarItem>
          <Link href={"/overview"} aria-current="page" color="foreground">
            {t('navigation.overview')}
          </Link>
        </NavbarItem>
        <NavbarItem>
          <Link href={"/profile"} aria-current="page" color="foreground">
            {t("navigation.profiles")}
          </Link>
        </NavbarItem>
        <Dropdown>
          <NavbarItem>
            <DropdownTrigger>
              <Button
                disableRipple
                className="p-0 bg-transparent text-base data-[hover=true]:bg-transparent"
                endContent={icons.chevron}
                radius="sm"
                variant="light"
              >
                {t("navigation.statistics.header")}
              </Button>
            </DropdownTrigger>
          </NavbarItem>
          <DropdownMenu
            aria-label="TrackInsights Statistis"
            className="w-[340px]"
            itemClasses={{
              base: "gap-4",
            }}
          >
            <DropdownItem
              key="dropdown.statistics.bestlist"
              description={t("navigation.statistics.bestlists.description")}
              startContent={icons.activity}
              className="text-foreground"
              href="/bestlist"
            >
              {t("navigation.statistics.bestlists.header")}
            </DropdownItem>
            <DropdownItem
              key="dropdown.statistics.records"
              description={t("navigation.statistics.records.description")}
              startContent={icons.flash}
              className="text-foreground"
              href="/records"
            >
              {t("navigation.statistics.records.header")}
            </DropdownItem>
          </DropdownMenu>
        </Dropdown>
        <NavbarItem>
          <Link href={"/calculator"} color="foreground">
            {t("navigation.calculator")}
          </Link>
        </NavbarItem>
      </NavbarContent>
      <NavbarContent justify="end">
        <Dropdown>
          <NavbarItem>
            <DropdownTrigger>
              <Button isIconOnly aria-label="Like" size="sm" variant="light">
                {icons.world}
              </Button>
            </DropdownTrigger>
          </NavbarItem>
          <DropdownMenu
            aria-label="TrackInsights Localization"
            className="w-[200px]"
            itemClasses={{
              base: "gap-4",
            }}
          >
            <DropdownItem
              key="dropdown.localization.english"
              startContent={icons.enFlag}
              onClick={() => handleLanguageChange("en")}
              className="text-foreground"
            >
              {t("localization.english")}
            </DropdownItem>
            <DropdownItem
              key="dropdown.localization.german"
              startContent={icons.deFlag}
              onClick={() => handleLanguageChange("de")}
              className="text-foreground"
            >
              {t("localization.german")}
            </DropdownItem>
          </DropdownMenu>
        </Dropdown>
        <NavbarItem>
          <DarkModeSwitcher />
        </NavbarItem>
      </NavbarContent>
      <NavbarMenu>
        <NavbarMenuItem key="overview">
          <Link onPress={() => setIsMenuOpen(false)} className="w-full text-base" href={"/overview"} color="foreground">
            {t('navigation.overview')}
          </Link>
        </NavbarMenuItem>
        <NavbarMenuItem key="profiles">
          <Link onPress={() => setIsMenuOpen(false)} className="w-full text-base" href={"/profile"} color="foreground">
            {t('navigation.profiles')}
          </Link>
        </NavbarMenuItem>
        <NavbarMenuItem key="dropdown">
          <Accordion itemClasses={accItemClasses} className="px-0" variant="light" isCompact={true}>
            <AccordionItem className="text-base" key="acc-1" aria-label="Accordion 1" title={t("navigation.statistics.header")}>
              <Link onPress={() => setIsMenuOpen(false)} className="pl-5 w-full text-base" href={"/bestlist"} color="foreground">
                {t("navigation.statistics.bestlists.header")}
              </Link>
              <Link onPress={() => setIsMenuOpen(false)} className="pl-5 w-full text-base" href={"/records"} color="foreground">
                {t("navigation.statistics.records.header")}
              </Link>
            </AccordionItem>
          </Accordion>
        </NavbarMenuItem>
        <NavbarMenuItem key="calculator">
          <Link onPress={() => setIsMenuOpen(false)} className="w-full text-base" href={"/calculator"} color="foreground">
            {t('navigation.calculator')}
          </Link>
        </NavbarMenuItem>
      </NavbarMenu>
    </Navbar>
  )
}

export default NavigationBar;
