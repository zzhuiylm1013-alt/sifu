/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : XY Cross-Slide Table Controller
  *                   STM32F103ZET6 + Nidec DA2Z123 Servo Drives
  ******************************************************************************
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "i2c.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "config.h"
#include "uart_handler.h"
#include "timer.h"
#include "motion.h"
#include "servo.h"
#include "oled.h"
#include "protocol.h"
#include "sys_tick.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */
/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
/* USER CODE BEGIN PV */
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */
  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/
  HAL_Init();

  /* USER CODE BEGIN Init */
  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */
  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_I2C1_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */

  /* Setup system tick */
  SysTick_Setup();

  /* Initialize application modules */
  UART_Handler_Init();
  Timer_Init();
  Motion_Init();
  Servo_Init();
  Protocol_Init();

  /* Enable TIM2 interrupt for motion (NVIC priority 0 = highest) */
  HAL_NVIC_SetPriority(TIM2_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(TIM2_IRQn);

  /* Initialize OLED */
  // OLED_Init();          // skip if OLED not connected
  // OLED_DrawTitle("XY Table Controller");

  /* Start UART RX interrupt */
  UART_Handler_StartRx();

  /* Send ready signal to PC */
  UART_Handler_Send("READY\n");

  uint32_t last_oled = 0;
  uint32_t last_pos_report = 0;

  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */

    /* 1. Process received UART commands */
    if (UART_Handler_HasCommand()) {
        char *cmd = UART_Handler_GetCommand();
        Protocol_Parse(cmd);
    }

    /* 2. Send protocol responses */
    if (Protocol_HasResponse()) {
        UART_Handler_Send(Protocol_GetResponse());
    }

    /* 3. Update motion engine (main loop hook) */
    Motion_Update();

    /* 4. Handle homing sequence */
    if (Servo_IsHoming()) {
        if (Servo_Home_Update()) {
            UART_Handler_Send("HOME DONE\n");
        }
    }

    /* 5. Check alarms — stop immediately if triggered */
    if (Servo_AlarmCheck()) {
        Servo_Disable();
        Motion_EmergencyStop();
        UART_Handler_Sendf("ALM %d\n", Servo_GetAlarmCode());
    }

    /* 6. Refresh OLED (every 200ms) — skip if not connected */
    // if (SysTick_CheckElapsed(&last_oled, OLED_REFRESH_MS)) {
    //     OLED_Update(Motion_GetX_mm(), Motion_GetY_mm(),
    //                 Motion_GetStateStr(), Motion_GetCurrentSpeed());
    // }

    /* 7. Report position after move complete */
    if (Motion_MoveComplete()) {
        UART_Handler_Sendf("POS X=%.2f Y=%.2f\n",
                           Motion_GetX_mm(), Motion_GetY_mm());
    }

    /* 8. Periodic position report during long moves (every 200ms) */
    if (Motion_IsRunning() && SysTick_CheckElapsed(&last_pos_report, POS_REPORT_MS)) {
        UART_Handler_Sendf("POS X=%.2f Y=%.2f\n",
                           Motion_GetX_mm(), Motion_GetY_mm());
    }
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
