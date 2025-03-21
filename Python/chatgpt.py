"""
Raycast Maze Game
=================

Dieses Spiel ist ein First-Person-Raycasting-Spiel mit einem zufällig generierten Labyrinth,
erstellt mittels Depth-First Search (DFS). Das Labyrinth wird als 2D-Gitter aufgebaut,
wobei die Wände texturiert und mit einem Beleuchtungs-Effekt gerendert werden.

Features:
- Einstellungsfenster vor Spielstart: Hier lassen sich Fenstergröße und weitere Optionen anpassen.
- MacOS-Optimierung: Durch geeignete Pygame-Flags wird die Menüleiste korrekt integriert.
- Gegner mit einfacher KI: Sie verfolgen den Spieler mit leichter Unvorhersehbarkeit.
- Überraschende, versteckte Funktion, die das Spielerlebnis erweitert (entdecke sie selbst!).

Benötigte Pakete: pygame, numpy
"""

import sys, math, random, time
import numpy as np
import pygame

# Konstanten für Farben, etc.
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY  = (100, 100, 100)
DARKGRAY = (40, 40, 40)
RED   = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE  = (0, 0, 255)

# Globale Einstellungen (können im Einstellungsfenster verändert werden)
SETTINGS = {
    "width": 800,
    "height": 600,
    "fov": math.pi / 3,  # 60° Sichtfeld
    "max_depth": 20,
    "maze_rows": 15,
    "maze_cols": 15,
    "player_speed": 3.0,
    "rot_speed": 0.05,
    "enemy_speed": 1.5,
    "num_enemies": 3,
}

# -----------------------------------------------------------
# DFS-basierte Labyrinth-Erzeugung
# -----------------------------------------------------------
def generate_maze(rows, cols):
    """
    Erzeugt ein Labyrinth als 2D-Array, in dem jede Zelle vier Wände (oben, rechts, unten, links) besitzt.
    Mit DFS werden zufällig Passagen erzeugt.
    """
    maze = np.ones((rows, cols, 4), dtype=bool)  # [oben, rechts, unten, links] True = Wand vorhanden
    visited = np.zeros((rows, cols), dtype=bool)
    
    def dfs(r, c):
        visited[r, c] = True
        # Mische die Richtungen zufällig
        directions = [(0, -1, 3, 1), (0, 1, 1, 3), (-1, 0, 0, 2), (1, 0, 2, 0)]
        random.shuffle(directions)
        for dr, dc, wall_curr, wall_next in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not visited[nr, nc]:
                # Entferne die Wand zwischen den Zellen
                maze[r, c, wall_curr] = False
                maze[nr, nc, wall_next] = False
                dfs(nr, nc)
                
    dfs(0, 0)  # Start bei oben links
    return maze

# -----------------------------------------------------------
# Spielerklasse
# -----------------------------------------------------------
class Player:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = SETTINGS["player_speed"]
        self.rot_speed = SETTINGS["rot_speed"]
        self.last_move_time = time.time()  # Für die versteckte Funktion

# -----------------------------------------------------------
# Gegnerklasse mit einfacher KI
# -----------------------------------------------------------
class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = SETTINGS["enemy_speed"]
        self.direction = random.uniform(0, 2 * math.pi)
    
    def update(self, player, maze, dt):
        """
        Gegner bewegt sich in Richtung des Spielers, mit etwas zufälliger Abweichung.
        Dabei wird überprüft, ob der Gegner den Spieler "sehen" kann (einfache Distanzmessung).
        """
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        # Gegner "sehen" den Spieler, wenn er in einem bestimmten Radius ist
        if dist < 8:
            # Leicht unvorhersehbare Bewegung in Richtung Spieler
            target_angle = math.atan2(dy, dx) + random.uniform(-0.2, 0.2)
            self.direction = target_angle
        # Update Position
        self.x += math.cos(self.direction) * self.speed * dt
        self.y += math.sin(self.direction) * self.speed * dt

# -----------------------------------------------------------
# Einstellungsmenü (Pre-Game Options)
# -----------------------------------------------------------
def options_menu():
    """
    Erzeugt ein einfaches Einstellungsfenster, in dem der Spieler die Fenstergröße und Gameplay-Optionen
    einstellen kann. Der Spieler kann per Tastendruck die voreingestellte Option bestätigen.
    """
    pygame.init()
    screen = pygame.display.set_mode((400, 300), pygame.RESIZABLE)  # RESIZABLE für macOS Menüintegration
    pygame.display.set_caption("Einstellungen - Raycast Maze")
    font = pygame.font.SysFont("Arial", 20)
    
    options = {
        "width": SETTINGS["width"],
        "height": SETTINGS["height"],
    }
    info_text = "Drücke ENTER, um fortzufahren"
    
    running = True
    while running:
        screen.fill(DARKGRAY)
        # Anzeige der aktuellen Optionen
        texts = [
            f"Fensterbreite (w/s): {options['width']}",
            f"Fensterhöhe (a/d): {options['height']}",
            info_text,
        ]
        for i, t in enumerate(texts):
            txt_surface = font.render(t, True, WHITE)
            screen.blit(txt_surface, (20, 20 + i * 40))
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                # Mit w/s Breite anpassen, a/d Höhe
                if event.key == pygame.K_w:
                    options["width"] += 50
                elif event.key == pygame.K_s:
                    options["width"] = max(400, options["width"] - 50)
                elif event.key == pygame.K_a:
                    options["height"] += 50
                elif event.key == pygame.K_d:
                    options["height"] = max(300, options["height"] - 50)
                elif event.key == pygame.K_RETURN:
                    running = False
    # Update globale Einstellungen
    SETTINGS["width"] = options["width"]
    SETTINGS["height"] = options["height"]
    pygame.quit()

# -----------------------------------------------------------
# Raycasting-Engine
# -----------------------------------------------------------
class Raycaster:
    def __init__(self, screen, maze, cell_size=1):
        self.screen = screen
        self.maze = maze
        self.rows, self.cols, _ = maze.shape
        self.cell_size = cell_size
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.fov = SETTINGS["fov"]
        self.max_depth = SETTINGS["max_depth"]
        # Erstelle einen einfachen "Textur"-Puffer: Wir generieren ein Muster
        self.wall_texture = self.generate_texture(64, 64)
    
    def generate_texture(self, w, h):
        """
        Erzeugt eine einfache texturierte Oberfläche mit einem Streifenmuster.
        """
        texture = pygame.Surface((w, h))
        for y in range(h):
            for x in range(w):
                # Streifenmuster
                color = (200, 200, 200) if (x // 8) % 2 == 0 else (150, 150, 150)
                texture.set_at((x, y), color)
        return texture.convert()
    
    def cast_rays(self, player):
        """
        Führt das Raycasting durch:
        Für jede senkrechte Linie (Spalte) im Fenster wird ein Strahl geworfen, um
        die Entfernung zur nächsten Wand zu ermitteln. Danach wird die entsprechende
        Textur-Spalte gerendert.
        """
        half_fov = self.fov / 2
        num_rays = self.width  # Ein Ray pro Bildschirmspalte
        delta_angle = self.fov / num_rays
        current_angle = player.angle - half_fov
        
        for ray in range(num_rays):
            # Berechne den Richtungsvektor des Strahls
            sin_a = math.sin(current_angle)
            cos_a = math.cos(current_angle)
            # Schrittweite, um Kollisionen zu ermitteln
            for depth in np.linspace(0.1, self.max_depth, 100):
                target_x = player.x + cos_a * depth
                target_y = player.y + sin_a * depth
                # Bestimme die Zelle im Labyrinth
                cell_x = int(target_x)
                cell_y = int(target_y)
                if cell_x < 0 or cell_x >= self.cols or cell_y < 0 or cell_y >= self.rows:
                    depth = self.max_depth
                    break
                # Bei einer Kollision mit einer Wand
                if self.is_wall(cell_y, cell_x):
                    break
            # Berechne die Höhe der Wand-Säule auf dem Bildschirm
            depth *= math.cos(player.angle - current_angle)  # Fisheye-Korrektur
            if depth == 0:
                depth = 0.0001
            wall_height = min(self.height, int(self.height / (depth + 0.0001)))
            # Berechne den Texturkoordinaten-Anteil
            texture_x = int((target_x - cell_x) * self.wall_texture.get_width()) % self.wall_texture.get_width()
            # Helligkeit basierend auf der Distanz
            shade = max(0.2, 1 - depth / self.max_depth)
            # Rendern der vertikalen Linie (Säule)
            column = pygame.transform.scale(self.wall_texture.subsurface((texture_x, 0, 1, self.wall_texture.get_height())), (1, wall_height))
            # Helligkeitsanpassung: Erzeuge einen dunklen Filter
            column.fill((int(255*shade), int(255*shade), int(255*shade)), special_flags=pygame.BLEND_MULT)
            # Zeichne die Säule
            x = ray
            y = (self.height - wall_height) // 2
            self.screen.blit(column, (x, y))
            current_angle += delta_angle
    
    def is_wall(self, row, col):
        """
        Prüft, ob in der Zelle (row, col) mindestens eine Wand vorhanden ist.
        Da das Labyrinth als DFS-Generierung erstellt wurde, betrachten wir
        eine Zelle als Wand, wenn sie nicht passierbar ist.
        """
        # Für Raycasting genügt eine einfache Prüfung: Wir rendern die Zellenränder als Wände.
        # Da das Labyrinth-Array nur Passagen entfernt, kann man annehmen, dass jede
        # nicht-erreichte Passage als Wand gilt.
        # Hier verwenden wir einen simplen Ansatz: Wenn die Zelle vollständig umgeben ist, gilt sie als Wand.
        walls = self.maze[row, col]
        return all(walls)

# -----------------------------------------------------------
# Hauptspielklasse
# -----------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        # Für macOS: RESIZABLE Flag integriert die native Menüleiste
        self.screen = pygame.display.set_mode((SETTINGS["width"], SETTINGS["height"]), pygame.RESIZABLE)
        pygame.display.set_caption("Raycast Maze")
        self.clock = pygame.time.Clock()
        self.maze = generate_maze(SETTINGS["maze_rows"], SETTINGS["maze_cols"])
        self.raycaster = Raycaster(self.screen, self.maze)
        # Setze den Spieler in die Startzelle
        self.player = Player(0.5, 0.5, 0)
        # Erzeuge Gegner an zufälligen Positionen (außerhalb der Startzelle)
        self.enemies = []
        for _ in range(SETTINGS["num_enemies"]):
            while True:
                ex = random.uniform(0, SETTINGS["maze_cols"])
                ey = random.uniform(0, SETTINGS["maze_rows"])
                if ex > 1 or ey > 1:  # Nicht in der Startzelle
                    self.enemies.append(Enemy(ex, ey))
                    break
        # Zeitvariable für die versteckte Funktion
        self.hidden_trigger_time = time.time()
        self.hidden_active = False

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0  # Delta-Time in Sekunden
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # macOS-spezifisch: Bei Fensteränderung aktualisieren wir die Bildschirmgröße
                if event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.raycaster.screen = self.screen
                    self.raycaster.width = event.w
                    self.raycaster.height = event.h
                    
            keys = pygame.key.get_pressed()
            # Spielerbewegung: Vorwärts, Rückwärts und Rotation
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                new_x = self.player.x + math.cos(self.player.angle) * self.player.speed * dt
                new_y = self.player.y + math.sin(self.player.angle) * self.player.speed * dt
                if not self.raycaster.is_wall(int(new_y), int(new_x)):
                    self.player.x = new_x
                    self.player.y = new_y
                    self.player.last_move_time = time.time()
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                new_x = self.player.x - math.cos(self.player.angle) * self.player.speed * dt
                new_y = self.player.y - math.sin(self.player.angle) * self.player.speed * dt
                if not self.raycaster.is_wall(int(new_y), int(new_x)):
                    self.player.x = new_x
                    self.player.y = new_y
                    self.player.last_move_time = time.time()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.player.angle -= self.player.rot_speed
                self.player.last_move_time = time.time()
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.player.angle += self.player.rot_speed
                self.player.last_move_time = time.time()
            
            # Aktualisiere Gegner
            for enemy in self.enemies:
                enemy.update(self.player, self.maze, dt)
            
            # Render-Schritt:
            self.screen.fill(BLACK)
            self.raycaster.cast_rays(self.player)
            
            # Optional: Zeichne Minimap (oben links) für Übersicht (einfache Darstellung)
            self.draw_minimap()
            
            # Versteckte Funktion: Wenn der Spieler über längere Zeit nahezu still steht, wird
            # ein überraschender visueller Effekt aktiviert.
            if time.time() - self.player.last_move_time > 5:
                self.hidden_active = True
            else:
                self.hidden_active = False
            if self.hidden_active:
                self.apply_hidden_effect()
            
            pygame.display.flip()
        pygame.quit()
    
    def draw_minimap(self):
        """
        Zeichnet eine kleine Übersichtskarte in der linken oberen Ecke,
        die das Labyrinth, den Spieler und die Gegner anzeigt.
        """
        map_scale = 8
        minimap = pygame.Surface((self.maze.shape[1] * map_scale, self.maze.shape[0] * map_scale))
        minimap.fill(BLACK)
        # Zeichne Zellen als Rechtecke
        for y in range(self.maze.shape[0]):
            for x in range(self.maze.shape[1]):
                color = GRAY if self.raycaster.is_wall(y, x) else DARKGRAY
                pygame.draw.rect(minimap, color, (x * map_scale, y * map_scale, map_scale, map_scale))
        # Zeichne Spieler als kleinen Kreis
        pygame.draw.circle(minimap, GREEN, (int(self.player.x * map_scale), int(self.player.y * map_scale)), 3)
        # Zeichne Gegner als rote Kreise
        for enemy in self.enemies:
            pygame.draw.circle(minimap, RED, (int(enemy.x * map_scale), int(enemy.y * map_scale)), 3)
        # Blit die Minimap in den Hauptbildschirm
        self.screen.blit(minimap, (10, 10))
    
    def apply_hidden_effect(self):
        """
        Diese Methode implementiert eine überraschende, versteckte Funktion:
        Ein visueller Effekt, der den Bildschirm für kurze Zeit verändert.
        (Hinweis: Die Funktion ist nicht direkt als "geheim" benannt.)
        """
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        # Erzeuge einen schimmernden, pulsierenden Farbeffekt
        alpha = int((math.sin(time.time()*3) + 1) / 2 * 128)
        overlay.fill((0, 0, 255))
        overlay.set_alpha(alpha)
        self.screen.blit(overlay, (0, 0))

# -----------------------------------------------------------
# Main-Funktion: Startet erst das Optionsmenü, danach das Spiel
# -----------------------------------------------------------
def main():
    # Zuerst das Einstellungsfenster anzeigen
    options_menu()
    # Spiel initialisieren und starten
    game = Game()
    game.run()

if __name__ == '__main__':
    main()
