class ModernAdminSettingsRuntimeService:
    """Hybrid-owned boundary for Modern settings runtime persistence.

    The service owns the Modern settings save intent. The default config adapter
    still delegates to the existing config implementation so persistence
    behavior stays unchanged.
    """

    def __init__(self, config_adapter_factory=None):
        self.config_adapter_factory = config_adapter_factory or self.default_config_adapter_factory


    def save_config_revision(self, config, username, note):
        config_adapter = self.config_adapter_factory()
        config_adapter.config = config
        return config_adapter.save(username, note)


    def default_config_adapter_factory(self):
        from .config import IndiAllSkyConfig

        return IndiAllSkyConfig()
