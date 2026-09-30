-- MOD03's product name is "Mangalya". The registry key stays 'mangaly' (it is
-- referenced by services, service keys and stored module data); only the name
-- members see on the ForKhatri hub changes.
UPDATE registry.module SET name = 'Mangalya' WHERE key = 'mangaly' AND name = 'Mangaly';
