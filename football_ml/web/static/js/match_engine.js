class MatchSimulation {
    constructor(canvasId, homeTeam, awayTeam, probs) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.width = this.canvas.width;
        this.height = this.canvas.height;

        this.homeTeam = homeTeam;
        this.awayTeam = awayTeam;
        this.probs = probs; 

        this.players = [];
        this.ball = { x: this.width / 2, y: this.height / 2, vx: 0, vy: 0, radius: 5 };
        this.score = { home: 0, away: 0 };
        this.penaltyScore = { home: 0, away: 0 };
        this.timer = 0; 
        this.isGameOver = false;
        this.matchStage = 'REGULAR'; 
        this.penaltyRound = 0;
        this.penaltyTurn = 'home'; 
        this.waitingForPenalty = false;

        this.initPlayers();
        this.lastUpdate = Date.now();
    }

    restart() {
        this.ball = { x: this.width / 2, y: this.height / 2, vx: 0, vy: 0, radius: 5 };
        this.score = { home: 0, away: 0 };
        this.penaltyScore = { home: 0, away: 0 };
        this.timer = 0;
        this.isGameOver = false;
        this.matchStage = 'REGULAR';
        this.penaltyRound = 0;
        this.penaltyTurn = 'home';
        this.waitingForPenalty = false;
        this.initPlayers();
        this.lastUpdate = Date.now();
        this.loop();
    }

    initPlayers() {
        this.players = [];
        for (let i = 0; i < 11; i++) {
            this.players.push({
                team: 'home',
                x: (Math.random() * 0.4 + 0.05) * this.width,
                y: Math.random() * this.height,
                id: i,
                speed: 1.5 + (this.probs.prob_home * 0.5)
            });
        }
        for (let i = 0; i < 11; i++) {
            this.players.push({
                team: 'away',
                x: (Math.random() * 0.4 + 0.55) * this.width,
                y: Math.random() * this.height,
                id: i + 11,
                speed: 1.5 + (this.probs.prob_away * 0.5)
            });
        }
    }

    update() {
        if (this.matchStage === 'FINISHED') return;

        const now = Date.now();
        const dt = (now - this.lastUpdate) / 1000;
        this.lastUpdate = now;

        if (this.matchStage !== 'PENALTIES') {
            this.timer += dt * 10; 
            
            if (this.matchStage === 'REGULAR' && this.timer >= 90) {
                if (this.score.home === this.score.away) {
                    this.matchStage = 'EXTRA';
                } else {
                    this.matchStage = 'FINISHED';
                }
            } else if (this.matchStage === 'EXTRA' && this.timer >= 120) {
                if (this.score.home === this.score.away) {
                    this.matchStage = 'PENALTIES';
                    this.timer = 120;
                    this.resetBall();
                } else {
                    this.matchStage = 'FINISHED';
                }
            }

            if (this.matchStage !== 'PENALTIES' && this.matchStage !== 'FINISHED') {
                this.updateGameplay();
            }
        } else {
            this.updatePenalties(dt);
        }
    }

    updateGameplay() {
        this.players.forEach(p => {
            const dx = this.ball.x - p.x;
            const dy = this.ball.y - p.y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist > 5) {
                p.x += (dx / dist) * p.speed;
                p.y += (dy / dist) * p.speed;
            }

            if (dist < 10) {
                const targetGoalX = p.team === 'home' ? this.width : 0;
                const targetGoalY = this.height / 2;
                const accuracy = p.team === 'home' ? this.probs.prob_home : this.probs.prob_away;
                const goalTendency = this.probs.prob_over_2_5;

                if (Math.random() < 0.05 * goalTendency) {
                    const gdx = targetGoalX - this.ball.x;
                    const gdy = targetGoalY - this.ball.y;
                    const gdist = Math.sqrt(gdx * gdx + gdy * gdy);
                    this.ball.vx = (gdx / gdist) * 10;
                    this.ball.vy = (gdy / gdist) * 10 + (Math.random() - 0.5) * (1 - accuracy) * 10;
                }
            }
        });

        this.ball.x += this.ball.vx;
        this.ball.y += this.ball.vy;
        this.ball.vx *= 0.98;
        this.ball.vy *= 0.98;

        if (this.ball.x >= this.width) {
            if (this.ball.y > this.height * 0.4 && this.ball.y < this.height * 0.6) {
                this.score.home++;
                this.resetBall();
            } else {
                this.ball.vx *= -1;
            }
        } else if (this.ball.x <= 0) {
            if (this.ball.y > this.height * 0.4 && this.ball.y < this.height * 0.6) {
                this.score.away++;
                this.resetBall();
            } else {
                this.ball.vx *= -1;
            }
        }
        if (this.ball.y <= 0 || this.ball.y >= this.height) this.ball.vy *= -1;
    }

    updatePenalties(dt) {
        if (!this.waitingForPenalty) {
            this.waitingForPenalty = true;
            setTimeout(() => {
                if (this.matchStage !== 'PENALTIES') return;
                const accuracy = this.penaltyTurn === 'home' ? this.probs.prob_home : this.probs.prob_away;
                const scored = Math.random() < (0.7 + accuracy * 0.2);
                if (scored) {
                    this.penaltyScore[this.penaltyTurn]++;
                }
                if (this.penaltyTurn === 'away') {
                    this.penaltyRound++;
                }
                this.penaltyTurn = this.penaltyTurn === 'home' ? 'away' : 'home';
                this.waitingForPenalty = false;
                if (this.penaltyRound >= 5 && this.penaltyTurn === 'home') {
                    if (this.penaltyScore.home !== this.penaltyScore.away) {
                        this.matchStage = 'FINISHED';
                    }
                }
            }, 2000);
        }
    }

    resetBall() {
        this.ball = { x: this.width / 2, y: this.height / 2, vx: 0, vy: 0, radius: 5 };
    }

    draw() {
        this.ctx.fillStyle = '#2e7d32';
        this.ctx.fillRect(0, 0, this.width, this.height);
        this.ctx.strokeStyle = 'rgba(255,255,255,0.5)';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(5, 5, this.width - 10, this.height - 10);
        this.ctx.beginPath();
        this.ctx.moveTo(this.width / 2, 0);
        this.ctx.lineTo(this.width / 2, this.height);
        this.ctx.stroke();
        this.ctx.beginPath();
        this.ctx.arc(this.width / 2, this.height / 2, 50, 0, Math.PI * 2);
        this.ctx.stroke();
        this.ctx.fillStyle = 'white';
        this.ctx.fillRect(0, this.height * 0.4, 5, this.height * 0.2);
        this.ctx.fillRect(this.width - 5, this.height * 0.4, 5, this.height * 0.2);

        if (this.matchStage !== 'PENALTIES') {
            this.players.forEach(p => {
                this.ctx.fillStyle = p.team === 'home' ? '#ffeb3b' : '#f44336';
                this.ctx.beginPath();
                this.ctx.arc(p.x, p.y, 8, 0, Math.PI * 2);
                this.ctx.fill();
                this.ctx.strokeStyle = 'black';
                this.ctx.stroke();
            });
            this.ctx.fillStyle = 'white';
            this.ctx.beginPath();
            this.ctx.arc(this.ball.x, this.ball.y, this.ball.radius, 0, Math.PI * 2);
            this.ctx.fill();
        } else {
            this.ctx.fillStyle = 'rgba(0,0,0,0.7)';
            this.ctx.fillRect(0, 0, this.width, this.height);
            this.ctx.fillStyle = 'white';
            this.ctx.font = 'bold 40px Inter';
            this.ctx.textAlign = 'center';
            this.ctx.fillText(`PENALTY SHOOTOUT`, this.width / 2, this.height / 2 - 80);
            this.ctx.font = 'bold 60px Inter';
            this.ctx.fillText(`${this.penaltyScore.home} - ${this.penaltyScore.away}`, this.width / 2, this.height / 2 + 20);
            this.ctx.font = '24px Inter';
            this.ctx.fillStyle = '#ffc107';
            this.ctx.fillText(`Round ${this.penaltyRound + 1} | Kicking: ${this.penaltyTurn.toUpperCase()}`, this.width / 2, this.height / 2 + 100);
        }
    }

    loop() {
        this.update();
        this.draw();
        if (this.matchStage !== 'FINISHED') {
            requestAnimationFrame(() => this.loop());
        }
        let scoreText = `${this.homeTeam} ${this.score.home} - ${this.score.away} ${this.awayTeam}`;
        if (this.matchStage === 'PENALTIES' || (this.matchStage === 'FINISHED' && this.penaltyScore.home + this.penaltyScore.away > 0)) {
            scoreText += ` (${this.penaltyScore.home} - ${this.penaltyScore.away} PK)`;
        }
        document.getElementById('scoreDisplay').innerText = scoreText;
        let stageLabel = this.matchStage === 'REGULAR' ? "" : ` (${this.matchStage})`;
        document.getElementById('timerDisplay').innerText = `Time: ${Math.floor(this.timer)}'${stageLabel}`;
        if (this.matchStage === 'FINISHED') {
            document.getElementById('reRunBtn').classList.remove('d-none');
        } else {
            document.getElementById('reRunBtn').classList.add('d-none');
        }
    }
}
