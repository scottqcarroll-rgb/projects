class BootScene extends Phaser.Scene {
  constructor() {
    super({ key: 'BootScene', active: true });
  }

  preload() {}

  create() {
    // Placeholder: confirm Phaser is loaded
    console.log('BootScene: Phaser loaded successfully');

    // Transition to MenuScene
    this.scene.start('MenuScene');
  }
}
