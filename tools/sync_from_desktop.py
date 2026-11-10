"""Synchronize dashboard/dist/index.js from desktop/plugin.js."""
import pathlib

p_desk = pathlib.Path("integrations/hermes/yadro-guard/desktop/plugin.js")
desk_txt = p_desk.read_text(encoding="utf-8")

start_marker = "const makeGuardPage = function (SDK, onReady) {"
end_marker = "onReady(GuardPage);\n};"

i = desk_txt.index(start_marker) + len(start_marker)
j = desk_txt.rindex(end_marker) + len("onReady(GuardPage);\n")
factory_body = desk_txt[i:j]

header = """  const AGENT_ICON_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAFO0lEQVR4nO2cP2sUQRjGb49DgshqLeRAuwgpFIvEKpIyXUrBjxG4fIIc5GMIlulSBlOZFKJFwOsMXMDaBJEggciCG5bN7u3Mzr/nnXl+jfFPbmbn+c07s7tjBgNCCCGEpEjms7G1o+tbn+1J5nRzyUs2Thth4PhCOPlQBi9HBKsfxuDliZD5Dn56Mtq10WbMTNZv9nyJkLkOn4G7F8JEgsxV+G3Bb+0vT0zaTIHDnYuprgh9JchcB8/A7QthU4TMVvhn288uqx1l8Papj+/qwfljUwkyG+FXZz2D9ytCWzVQlWBo2hmG75/qJDPdZA9NZj/Dx5VA9dY8Mw2fJR9nSWhaDrqWgqHpzCc49KkE2nuAYrdffs3Zj0E1h2o+KiwsDyz98S8FWhWA676MSqCzRLcKwDd7cdGWp3IF4OyPswo0CsDZHydNuSpVAM7+eKuA8aNgIhsKkDj3BOD6Hzf1fDsrANf/uPcBXAIShwIkDgVIHAqQOBQgcShA4lCAxBkNhPL718/GM/EhefTkqdZpHARECYAYelv/pMgwkhr81Z+/AzTyhw/u9RldhKG08IvgEcNv6xt61YIWoDp4yMHXqfcVWQJYAcpBkxR8nWrfUSUYoocfA1fAEsAJEFv46BJACRBr+MgSwAiANCgpXS+MACWxzn7U64MQAGU2pHjdEAKgzo4UrhNKAJKgALHv/NHvCIILQMIi4m1gE+PnL1v/bv7jW3TtukJkBVgUgsrfS2s3agG+fJ9r/XvVQbYdxthRu7rXH5UAx59PtTZAuoNrS4Kx43Z1xyEKAVyHb/p9vtsNJUGQTaDNi135+PXu69m7V7Y+Nki7xbhsvFm7jLoCuAq/6feuWHHYru9K4FWAkGudJI49jtNQ6kW1zTrXVWDFU7u+JPAmgO+1TTobnsbL6xJACfDGyfsmkBIsJvq7gAJKgDMuwR4EUQKM8Qj6KJgShB+H4C+DXr8Y9/q+tqdvrp8Gziy32/f6oxGAhEW0APVZ5+tdwCxQuy4QeyIo9ODPBIcusgL0PW5lekxrHqhdX4gRoM+g2gphHqhdH4gSQGdwbYcwD9Sua8QJoDLIrkKYB2rXJWI3gaEGey4w5OgqALEHBUgcCpA4wQUof5Bi9YcspkD+/3pD/yDJ4AKQsEAJkEoVyIGuE+I2sCiDtv+f/IeDTwPbvN9+a/XzQpd/uAqANjtSuD6ICuCiCtierbZBmP1wFSD2O4IcZOcPK0DMEuSA4UMKEKMEOWj4sALUJZAqQl7pO2L40ALUB02SCHmtr6jhwwvQNHjIIuQNfUMOH+o2cBHlIFZvE1ElkBK8KAGaBjX0T9iUHLpYAaQPNiLwewDiFgqQOBQgcShA4lCAxKEAiUMBEqdTgMn6zV7x6+HOxdRLj4gVyrzK/JQFON1cyux0gSBSz5dLQOJQgMRREoD7gDjX/1YBuA+Ik6ZclZcAVoH4Zv9CAVgF4qItT61NIKtAXLO/U4Ama7b2lyfVxggGZR5lPqrVXPs2cPXg/O4oFiXAoJpDNR8VOgVoskenxBB/NOXStZdTfuy7dnR9W/+z6clot/y6qfQQfzO/T/haS0BXJeByIC98K4+CKQFe+Dpov/lrWgoKzrafXVY7xiXBPvXxbdvw6TzD6fXqt02C+r6ggCKYU19eF8163Qd4Ru/+dUQooRDdtO2nbAZfYnz4Y5EEi0Qg6nSt8yaP7a2c/umSoAqF6EZnY2f6zsbq8S8dEYgZtl7WOTn/RxHcYfstrdMDoBTBHq5ez3s9AUwh1OF5DEIIIQO3/AN947ipvZc6YgAAAABJRU5ErkJggg==";
/* mcp-secrets-guard — Hermes dashboard tab.
 * Plain IIFE, no build step. React + fetchJSON come from the host via
 * window.__HERMES_PLUGIN_SDK__. All text is rendered through React (auto-escaped);
 * no innerHTML anywhere. HTML reports open in a sandboxed iframe (no scripts). */
(function (SDK, onReady) {"""

footer = """})(window.__HERMES_PLUGIN_SDK__, function (GuardPage) {
  if (window.__HERMES_PLUGINS__ && typeof window.__HERMES_PLUGINS__.register === "function") {
    window.__HERMES_PLUGINS__.register("yadro-guard", GuardPage);
  }
});
"""

new_index = header + factory_body + footer
target_path = pathlib.Path("integrations/hermes/yadro-guard/dashboard/dist/index.js")
target_path.write_text(new_index, encoding="utf-8")
print("Reconstructed dashboard/dist/index.js from desktop/plugin.js, size:", len(new_index))

