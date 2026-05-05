// Global event bus
window.GameEvents = new Phaser.Events.EventEmitter();

const config = {
  type: Phaser.AUTO,
  width: 800,
  height: 600,
  backgroundColor: '#1a1a2e',
  render: {
    pixelArt: true,
    antialias: false,
  },
  physics: {
    default: 'arcade',
    arcade: {
      gravity: { y: 0 },
      debug: false,
    },
  },
  scene: [
    BootScene,
    MenuScene,
    GameScene,
    HUDScene,
    PauseScene,
    GameOverScene,
  ],
};

const game = new Phaser.Game(config);
